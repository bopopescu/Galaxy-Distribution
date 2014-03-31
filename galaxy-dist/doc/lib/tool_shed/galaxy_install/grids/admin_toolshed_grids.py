import logging

from galaxy import model, util
from galaxy.web.framework.helpers import iff, grids
from galaxy.model.orm import or_
import tool_shed.util.shed_util_common as suc
from tool_shed.util import tool_dependency_util

log = logging.getLogger( __name__ )

def generate_deprecated_repository_img_str( include_mouse_over=False ):
    if include_mouse_over:
        deprecated_tip_str = 'class="icon-button" title="This repository is deprecated in the Tool Shed"'
    else:
        deprecated_tip_str = ''
    return '<img src="/static/images/icon_error_sml.gif" %s/>' % deprecated_tip_str

def generate_includes_workflows_img_str( include_mouse_over=False ):
    if include_mouse_over:
        deprecated_tip_str = 'class="icon-button" title="This repository contains exported workflows"'
    else:
        deprecated_tip_str = ''
    return '<img src="/static/images/fugue/gear.png" %s/>' % deprecated_tip_str

def generate_latest_revision_img_str( include_mouse_over=False ):
    if include_mouse_over:
        latest_revision_tip_str = 'class="icon-button" title="This is the latest installable revision of this repository"'
    else:
        latest_revision_tip_str = ''
    return '<img src="/static/june_2007_style/blue/ok_small.png" %s/>' % latest_revision_tip_str

def generate_revision_updates_img_str( include_mouse_over=False ):
    if include_mouse_over:
        revision_updates_tip_str = 'class="icon-button" title="Updates are available in the Tool Shed for this revision"'
    else:
        revision_updates_tip_str = ''
    return '<img src="/static/images/icon_warning_sml.gif" %s/>' % revision_updates_tip_str

def generate_revision_upgrades_img_str( include_mouse_over=False ):
    if include_mouse_over:
        revision_upgrades_tip_str = 'class="icon-button" title="A newer installable revision is available for this repository"'
    else:
        revision_upgrades_tip_str = ''
    return '<img src="/static/images/up.gif" %s/>' % revision_upgrades_tip_str

def generate_unknown_img_str( include_mouse_over=False ):
    if include_mouse_over:
        unknown_tip_str = 'class="icon-button" title="Unable to get information from the Tool Shed"'
    else:
        unknown_tip_str = ''
    return '<img src="/static/june_2007_style/blue/question-octagon-frame.png" %s/>' % unknown_tip_str


class InstalledRepositoryGrid( grids.Grid ):


    class ToolShedStatusColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            if tool_shed_repository.tool_shed_status:
                tool_shed_status_str = ''
                if tool_shed_repository.is_deprecated_in_tool_shed:
                    tool_shed_status_str += generate_deprecated_repository_img_str( include_mouse_over=True )
                if tool_shed_repository.is_latest_installable_revision:
                    tool_shed_status_str += generate_latest_revision_img_str( include_mouse_over=True )
                if tool_shed_repository.revision_update_available:
                    tool_shed_status_str += generate_revision_updates_img_str( include_mouse_over=True )
                if tool_shed_repository.upgrade_available:
                    tool_shed_status_str += generate_revision_upgrades_img_str( include_mouse_over=True )
                if tool_shed_repository.includes_workflows:
                    tool_shed_status_str += generate_includes_workflows_img_str( include_mouse_over=True )
            else:
                tool_shed_status_str = generate_unknown_img_str( include_mouse_over=True )
            return tool_shed_status_str


    class NameColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return str( tool_shed_repository.name )


    class DescriptionColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return util.unicodify( tool_shed_repository.description )


    class OwnerColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return str( tool_shed_repository.owner )


    class RevisionColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return str( tool_shed_repository.changeset_revision )


    class StatusColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return suc.get_tool_shed_repository_status_label( trans, tool_shed_repository )


    class ToolShedColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return tool_shed_repository.tool_shed


    class DeletedColumn( grids.DeletedColumn ):

            def get_accepted_filters( self ):
                """ Returns a list of accepted filters for this column. """
                accepted_filter_labels_and_vals = { "Active" : "False", "Deactivated or uninstalled" : "True", "All": "All" }
                accepted_filters = []
                for label, val in accepted_filter_labels_and_vals.items():
                   args = { self.key: val }
                   accepted_filters.append( grids.GridColumnFilter( label, args) )
                return accepted_filters
    # Grid definition
    title = "Installed tool shed repositories"
    model_class = model.ToolShedRepository
    template='/admin/tool_shed_repository/grid.mako'
    default_sort_key = "name"
    columns = [
        ToolShedStatusColumn( "",
                              attach_popup=False ),
        NameColumn( "Name",
                    key="name",
                    link=( lambda item: iff( item.status in [ model.ToolShedRepository.installation_status.CLONING ],
                                             None,
                                             dict( operation="manage_repository", id=item.id ) ) ),
                    attach_popup=True ),
        DescriptionColumn( "Description" ),
        OwnerColumn( "Owner" ),
        RevisionColumn( "Revision" ),
        StatusColumn( "Installation Status",
                      filterable="advanced" ),
        ToolShedColumn( "Tool shed" ),
        # Columns that are valid for filtering but are not visible.
        DeletedColumn( "Status",
                       key="deleted",
                       visible=False,
                       filterable="advanced" )
    ]
    columns.append( grids.MulticolFilterColumn( "Search repository name",
                                                cols_to_filter=[ columns[0] ],
                                                key="free-text-search",
                                                visible=False,
                                                filterable="standard" ) )
    global_actions = [
        grids.GridAction( "Update tool shed status",
                          dict( controller='admin_toolshed', action='update_tool_shed_status_for_installed_repository', all_installed_repositories=True ) )
    ]
    operations = [ grids.GridOperation( "Update tool shed status",
                                        allow_multiple=False,
                                        condition=( lambda item: not item.deleted ),
                                        async_compatible=False,
                                        url_args=dict( controller='admin_toolshed', action='browse_repositories', operation='update tool shed status' ) ),
                   grids.GridOperation( "Get updates",
                                        allow_multiple=False,
                                        condition=( lambda item: not item.deleted and item.revision_update_available and item.status not in \
                                            [ model.ToolShedRepository.installation_status.ERROR, model.ToolShedRepository.installation_status.NEW ] ),
                                        async_compatible=False,
                                        url_args=dict( controller='admin_toolshed', action='browse_repositories', operation='get updates' ) ),
                   grids.GridOperation( "Install",
                                        allow_multiple=False,
                                        condition=( lambda item: not item.deleted and item.status == model.ToolShedRepository.installation_status.NEW ),
                                        async_compatible=False,
                                        url_args=dict( controller='admin_toolshed', action='manage_repository', operation='install' ) ),
                   grids.GridOperation( "Deactivate or uninstall",
                                        allow_multiple=False,
                                        condition=( lambda item: not item.deleted and item.status not in \
                                            [ model.ToolShedRepository.installation_status.ERROR, model.ToolShedRepository.installation_status.NEW ] ),
                                        async_compatible=False,
                                        url_args=dict( controller='admin_toolshed', action='browse_repositories', operation='deactivate or uninstall' ) ),
                   grids.GridOperation( "Reset to install",
                                        allow_multiple=False,
                                        condition=( lambda item: ( item.status == model.ToolShedRepository.installation_status.ERROR ) ),
                                        async_compatible=False,
                                        url_args=dict( controller='admin_toolshed', action='browse_repositories', operation='reset to install' ) ),
                   grids.GridOperation( "Activate or reinstall",
                                        allow_multiple=False,
                                        condition=( lambda item: item.deleted ),
                                        async_compatible=False,
                                        url_args=dict( controller='admin_toolshed', action='browse_repositories', operation='activate or reinstall' ) ) ]
    standard_filters = []
    default_filter = dict( deleted="False" )
    num_rows_per_page = 50
    preserve_state = False
    use_paging = False

    def build_initial_query( self, trans, **kwd ):
        return trans.sa_session.query( self.model_class ) \
                               .order_by( self.model_class.table.c.tool_shed,
                                          self.model_class.table.c.name,
                                          self.model_class.table.c.owner,
                                          self.model_class.table.c.ctx_rev )

    @property
    def legend( self ):
        legend_str = '%s&nbsp;&nbsp;Updates are available in the Tool Shed for this revision<br/>' % generate_revision_updates_img_str()
        legend_str += '%s&nbsp;&nbsp;A newer installable revision is available for this repository<br/>' % generate_revision_upgrades_img_str()
        legend_str += '%s&nbsp;&nbsp;This is the latest installable revision of this repository<br/>' % generate_latest_revision_img_str()
        legend_str += '%s&nbsp;&nbsp;This repository is deprecated in the Tool Shed<br/>' % generate_deprecated_repository_img_str()
        legend_str += '%s&nbsp;&nbsp;This repository contains exported workflows<br/>' % generate_includes_workflows_img_str()
        legend_str += '%s&nbsp;&nbsp;Unable to get information from the Tool Shed<br/>' % generate_unknown_img_str()
        return legend_str


class RepositoryInstallationGrid( grids.Grid ):


    class NameColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return tool_shed_repository.name


    class DescriptionColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return tool_shed_repository.description


    class OwnerColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return tool_shed_repository.owner


    class RevisionColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            return tool_shed_repository.changeset_revision


    class StatusColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_shed_repository ):
            status_label = tool_shed_repository.status
            if tool_shed_repository.status in [ trans.model.ToolShedRepository.installation_status.CLONING,
                                                trans.model.ToolShedRepository.installation_status.SETTING_TOOL_VERSIONS,
                                                trans.model.ToolShedRepository.installation_status.INSTALLING_TOOL_DEPENDENCIES,
                                                trans.model.ToolShedRepository.installation_status.LOADING_PROPRIETARY_DATATYPES ]:
                bgcolor = trans.model.ToolShedRepository.states.INSTALLING
            elif tool_shed_repository.status in [ trans.model.ToolShedRepository.installation_status.NEW,
                                                 trans.model.ToolShedRepository.installation_status.UNINSTALLED ]:
                bgcolor = trans.model.ToolShedRepository.states.UNINSTALLED
            elif tool_shed_repository.status in [ trans.model.ToolShedRepository.installation_status.ERROR ]:
                bgcolor = trans.model.ToolShedRepository.states.ERROR
            elif tool_shed_repository.status in [ trans.model.ToolShedRepository.installation_status.DEACTIVATED ]:
                bgcolor = trans.model.ToolShedRepository.states.WARNING
            elif tool_shed_repository.status in [ trans.model.ToolShedRepository.installation_status.INSTALLED ]:
                if tool_shed_repository.missing_tool_dependencies or tool_shed_repository.missing_repository_dependencies:
                    bgcolor = trans.model.ToolShedRepository.states.WARNING
                if tool_shed_repository.missing_tool_dependencies and not tool_shed_repository.missing_repository_dependencies:
                    status_label = '%s, missing tool dependencies' % status_label
                if tool_shed_repository.missing_repository_dependencies and not tool_shed_repository.missing_tool_dependencies:
                    status_label = '%s, missing repository dependencies' % status_label
                if tool_shed_repository.missing_tool_dependencies and tool_shed_repository.missing_repository_dependencies:
                    status_label = '%s, missing both tool and repository dependencies' % status_label
                if not tool_shed_repository.missing_tool_dependencies and not tool_shed_repository.missing_repository_dependencies:
                    bgcolor = trans.model.ToolShedRepository.states.OK
            else:
                bgcolor = trans.model.ToolShedRepository.states.ERROR
            rval = '<div class="count-box state-color-%s" id="RepositoryStatus-%s">%s</div>' % \
                ( bgcolor, trans.security.encode_id( tool_shed_repository.id ), status_label )
            return rval

    title = "Monitor installing tool shed repositories"
    template = "admin/tool_shed_repository/repository_installation_grid.mako"
    model_class = model.ToolShedRepository
    default_sort_key = "-create_time"
    num_rows_per_page = 50
    preserve_state = True
    use_paging = False
    columns = [
        NameColumn( "Name",
                    link=( lambda item: iff( item.status in \
                                             [ model.ToolShedRepository.installation_status.NEW,
                                               model.ToolShedRepository.installation_status.CLONING,
                                               model.ToolShedRepository.installation_status.SETTING_TOOL_VERSIONS,
                                               model.ToolShedRepository.installation_status.INSTALLING_REPOSITORY_DEPENDENCIES,
                                               model.ToolShedRepository.installation_status.INSTALLING_TOOL_DEPENDENCIES,
                                               model.ToolShedRepository.installation_status.LOADING_PROPRIETARY_DATATYPES,
                                               model.ToolShedRepository.installation_status.UNINSTALLED ], \
                                             None, dict( action="manage_repository", id=item.id ) ) ),
                    filterable="advanced" ),
        DescriptionColumn( "Description",
                    filterable="advanced" ),
        OwnerColumn( "Owner",
                    filterable="advanced" ),
        RevisionColumn( "Revision",
                    filterable="advanced" ),
        StatusColumn( "Installation Status",
                      filterable="advanced",
                      label_id_prefix="RepositoryStatus-" )
    ]
    operations = []

    def build_initial_query( self, trans, **kwd ):
        clause_list = []
        tool_shed_repository_ids = util.listify( kwd.get( 'tool_shed_repository_ids', None ) )
        if tool_shed_repository_ids:
            for tool_shed_repository_id in tool_shed_repository_ids:
                clause_list.append( self.model_class.table.c.id == trans.security.decode_id( tool_shed_repository_id ) )
            if clause_list:
                return trans.sa_session.query( self.model_class ) \
                                       .filter( or_( *clause_list ) )
        for tool_shed_repository in trans.sa_session.query( self.model_class ) \
                                                    .filter( self.model_class.table.c.deleted == False ):
            if tool_shed_repository.status in [ trans.model.ToolShedRepository.installation_status.NEW,
                                               trans.model.ToolShedRepository.installation_status.CLONING,
                                               trans.model.ToolShedRepository.installation_status.SETTING_TOOL_VERSIONS,
                                               trans.model.ToolShedRepository.installation_status.INSTALLING_TOOL_DEPENDENCIES,
                                               trans.model.ToolShedRepository.installation_status.LOADING_PROPRIETARY_DATATYPES ]:
                clause_list.append( self.model_class.table.c.id == tool_shed_repository.id )
        if clause_list:
            return trans.sa_session.query( self.model_class ) \
                                   .filter( or_( *clause_list ) )
        return trans.sa_session.query( self.model_class ) \
                               .filter( self.model_class.table.c.status == trans.model.ToolShedRepository.installation_status.NEW )

    def apply_query_filter( self, trans, query, **kwd ):
        tool_shed_repository_id = kwd.get( 'tool_shed_repository_id', None )
        if tool_shed_repository_id:
            return query.filter_by( tool_shed_repository_id=trans.security.decode_id( tool_shed_repository_id ) )
        return query


class ToolDependencyGrid( grids.Grid ):


    class NameColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_dependency ):
            return tool_dependency.name


    class VersionColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_dependency ):
            return tool_dependency.version


    class TypeColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_dependency ):
            return tool_dependency.type


    class StatusColumn( grids.TextColumn ):

        def get_value( self, trans, grid, tool_dependency ):
            if tool_dependency.status in [ trans.model.ToolDependency.installation_status.INSTALLING ]:
                bgcolor = trans.model.ToolDependency.states.INSTALLING
            elif tool_dependency.status in [ trans.model.ToolDependency.installation_status.NEVER_INSTALLED,
                                             trans.model.ToolDependency.installation_status.UNINSTALLED ]:
                bgcolor = trans.model.ToolDependency.states.UNINSTALLED
            elif tool_dependency.status in [ trans.model.ToolDependency.installation_status.ERROR ]:
                bgcolor = trans.model.ToolDependency.states.ERROR
            elif tool_dependency.status in [ trans.model.ToolDependency.installation_status.INSTALLED ]:
                bgcolor = trans.model.ToolDependency.states.OK
            rval = '<div class="count-box state-color-%s" id="ToolDependencyStatus-%s">%s</div>' % \
                ( bgcolor, trans.security.encode_id( tool_dependency.id ), tool_dependency.status )
            return rval

    title = "Tool Dependencies"
    template = "admin/tool_shed_repository/tool_dependencies_grid.mako"
    model_class = model.ToolDependency
    default_sort_key = "-create_time"
    num_rows_per_page = 50
    preserve_state = True
    use_paging = False
    columns = [
        NameColumn( "Name",
                    link=( lambda item: iff( item.status in [ model.ToolDependency.installation_status.NEVER_INSTALLED,
                                                              model.ToolDependency.installation_status.INSTALLING,
                                                              model.ToolDependency.installation_status.UNINSTALLED ],
                                             None,
                                             dict( action="manage_tool_dependencies", operation='browse', id=item.id ) ) ),
                    filterable="advanced" ),
        VersionColumn( "Version",
                       filterable="advanced" ),
        TypeColumn( "Type",
                    filterable="advanced" ),
        StatusColumn( "Installation Status",
                      filterable="advanced" ),
    ]

    def build_initial_query( self, trans, **kwd ):
        tool_dependency_ids = tool_dependency_util.get_tool_dependency_ids( as_string=False, **kwd )
        if tool_dependency_ids:
            clause_list = []
            for tool_dependency_id in tool_dependency_ids:
                clause_list.append( self.model_class.table.c.id == trans.security.decode_id( tool_dependency_id ) )
            return trans.sa_session.query( self.model_class ) \
                                   .filter( or_( *clause_list ) )
        return trans.sa_session.query( self.model_class )

    def apply_query_filter( self, trans, query, **kwd ):
        tool_dependency_id = kwd.get( 'tool_dependency_id', None )
        if tool_dependency_id:
            return query.filter_by( tool_dependency_id=trans.security.decode_id( tool_dependency_id ) )
        return query