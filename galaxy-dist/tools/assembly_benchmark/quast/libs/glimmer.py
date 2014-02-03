############################################################################
# Copyright (c) 2011-2013 Saint-Petersburg Academic University
# All Rights Reserved
# See file LICENSE for details.
############################################################################

from __future__ import with_statement
import os
import tempfile
import subprocess
import itertools
import csv
import shutil

from libs import reporting, qconfig, qutils
from libs.fastaparser import read_fasta, write_fasta, rev_comp

from libs.log import get_logger
logger = get_logger(qconfig.LOGGER_DEFAULT_NAME)


def merge_gffs(gffs, out_path):
    '''Merges all GFF files into a single one, dropping GFF header.'''
    with open(out_path, 'w') as out_file:
        out_file.write('##gff-version 3\n')
        for gff_path in gffs:
            with open(gff_path, 'r') as gff_file:
                out_file.writelines(itertools.islice(gff_file, 2, None))

    return out_path


def parse_gff(gff_path):
    with open(gff_path) as gff_file:
        r = csv.reader(
            itertools.ifilter(lambda l: not l.startswith("#"), gff_file),
            delimiter='\t')
        for id, _source, type, start, end, score, strand, phase, extra in r:
            if type != 'mRNA':
                continue  # We're only interested in genes here.

            attrs = dict(kv.split("=") for kv in extra.split(";"))
            yield id, attrs.get('Name'), int(start), int(end), strand


def glimmerHMM(tool_dir, fasta_path, out_fpath, gene_lengths, err_path, tmp_dir):
    def run(contig_path, tmp_path):
        with open(err_path, 'a') as err_file:
            p = subprocess.call([tool_exec, contig_path,
                                 '-d', trained_dir,
                                 '-g', '-o', tmp_path],
                stdout=err_file, stderr=err_file)
            assert p is 0

    tool_exec = os.path.join(tool_dir, 'glimmerhmm')

    # Note: why arabidopsis? for no particular reason, really.
    trained_dir = os.path.join(tool_dir, 'trained', 'arabidopsis')

    contigs = {}
    gffs = []
    base_dir = tempfile.mkdtemp(dir=tmp_dir)
    for id, seq in read_fasta(fasta_path):
        contig_path = os.path.join(base_dir, id + '.fasta')
        gff_path = os.path.join(base_dir, id + '.gff')

        write_fasta(contig_path, [(id, seq)])
        run(contig_path, gff_path)
        gffs.append(gff_path)
        contigs[id] = seq

    out_gff_path = merge_gffs(gffs, out_fpath + '_genes.gff')
    #out_fasta_path = out_path + '_genes.fasta'
    unique, total = set(), 0
    #genes = []
    cnt = [0] * len(gene_lengths)
    for contig, gene_id, start, end, strand in parse_gff(out_gff_path):
        total += 1

        if strand == '+':
            gene_seq = contigs[contig][start:end + 1]
        else:
            gene_seq = rev_comp(contigs[contig][start:end + 1])

        if gene_seq not in unique:
            unique.add(gene_seq)

        #genes.append((gene_id, gene_seq))

        for idx, gene_length in enumerate(gene_lengths):
            cnt[idx] += end - start > gene_length

    #write_fasta(out_fasta_path, genes)
    if not qconfig.debug:
        shutil.rmtree(base_dir)

    #return out_gff_path, out_fasta_path, len(unique), total, cnt
    return out_gff_path, len(unique), total, cnt


def predict_genes(i, contigs_fpath, gene_lengths, out_dirpath, tool_dirpath, tmp_dirpath):
    assembly_name = qutils.name_from_fpath(contigs_fpath)
    assembly_label = qutils.label_from_fpath(contigs_fpath)

    logger.info('  ' + qutils.index_to_str(i) + assembly_label)

    out_fpath = os.path.join(out_dirpath, assembly_name + '_glimmer.stdout')
    err_fpath = os.path.join(out_dirpath, assembly_name + '_glimmer.stderr')
    #out_gff_path, out_fasta_path, unique, total, cnt = glimmerHMM(tool_dir,
    #    fasta_path, out_path, gene_lengths, err_path)
    out_gff_path, unique, total, cnt = glimmerHMM(tool_dirpath,
        contigs_fpath, out_fpath, gene_lengths, err_fpath, tmp_dirpath)
    logger.info('  ' + qutils.index_to_str(i) + '  Genes = ' + str(unique) + ' unique, ' + str(total) + ' total')
    logger.info('  ' + qutils.index_to_str(i) + '  Predicted genes (GFF): ' + out_gff_path)

    logger.info('  ' + qutils.index_to_str(i) + 'Gene prediction is finished.')
    return unique, cnt


def do(contigs_fpaths, gene_lengths, out_dirpath):
    logger.print_timestamp()
    logger.info('Running GlimmerHMM...')

    tool_dirpath = os.path.join(qconfig.LIBS_LOCATION, 'glimmer')
    tool_src_dirpath = os.path.join(tool_dirpath, 'src')
    tool_exec_fpath = os.path.join(tool_dirpath, 'glimmerhmm')
    tmp_dirpath = os.path.join(out_dirpath, 'tmp')

    if not os.path.isfile(tool_exec_fpath):
        # making
        logger.info("Compiling GlimmerHMM...")
        try:
            subprocess.call(
                ['make', '-C', tool_src_dirpath],
                stdout=open(os.path.join(tool_src_dirpath, 'make.log'), 'w'),
                stderr=open(os.path.join(tool_src_dirpath, 'make.err'), 'w'))
            if not os.path.isfile(tool_exec_fpath):
                raise
        except:
            logger.error("Failed to compile GlimmerHMM (" + tool_src_dirpath +
                         ")! Try to compile it manually or set --disable-gene-finding "
                         "option!")

    if not os.path.isdir(out_dirpath):
        os.makedirs(out_dirpath)
    if not os.path.isdir(tmp_dirpath):
        os.makedirs(tmp_dirpath)

    n_jobs = min(len(contigs_fpaths), qconfig.max_threads)
    from joblib import Parallel, delayed
    results = Parallel(n_jobs=n_jobs)(delayed(predict_genes)(
        i, contigs_fpath, gene_lengths, out_dirpath, tool_dirpath, tmp_dirpath)
        for i, contigs_fpath in enumerate(contigs_fpaths))

    # saving results
    for i, contigs_fpath in enumerate(contigs_fpaths):
        report = reporting.get(contigs_fpath)
        unique, cnt = results[i]
        report.add_field(reporting.Fields.PREDICTED_GENES_UNIQUE, unique)
        report.add_field(reporting.Fields.PREDICTED_GENES, cnt)

    if not qconfig.debug:
        shutil.rmtree(tmp_dirpath)

    logger.info('  Done.')