/**
 * Simple base model for any visible element. Includes useful attributes and ability
 * to set and track visibility.
 */
var BaseModel = Backbone.RelationalModel.extend({
    defaults: {
        name: null,
        hidden: false
    },
    
    show: function() {
        this.set("hidden", false);
    },
    
    hide: function() {
        this.set("hidden", true);
    },
    
    is_visible: function() {
        return !this.attributes.hidden;
    }
});


/**
 * Base view that handles visibility based on model's hidden attribute.
 */
var BaseView = Backbone.View.extend({
    
    initialize: function() {
        this.model.on("change:hidden", this.update_visible, this);
        this.update_visible();
    },
    
    update_visible: function() {
        if( this.model.attributes.hidden ){
            this.$el.hide();
        } else {
            this.$el.show();
        }
    }
});


//==============================================================================
/** @class Mixin to add logging capabilities to an object.
 *      Designed to allow switching an objects log output off/on at one central
 *      statement. Can be used with plain browser console (or something more
 *      complex like an AJAX logger).
 *  <br />NOTE: currently only uses the console.debug log function
 *  (as opposed to debug, error, warn, etc.)
 *  @name LoggableMixin
 *
 *  @example
 *  // Add to your models/views at the definition using chaining:
 *      var MyModel = BaseModel.extend( LoggableMixin ).extend({ // ... });
 * 
 *  // or - more explicitly AFTER the definition:
 *      var MyModel = BaseModel.extend({
 *          logger  : console
 *          // ...
 *          this.log( '$#%& it! - broken already...' );
 *      })
 *      _.extend( MyModel.prototype, LoggableMixin )
 *
 */
var LoggableMixin =  /** @lends LoggableMixin# */{

    /** The logging object whose log function will be used to output
     *      messages. Null will supress all logging. Commonly set to console.
     */
    // replace null with console (if available) to see all logs
    logger      : null,
    
    /** Output log messages/arguments to logger.
     *  @param {Arguments} ... (this function is variadic)
     *  @returns undefined if not this.logger
     */
    log : function(){
        if( this.logger ){
            var log = this.logger.log;
            if( typeof this.logger.log === 'object' ){
                log = Function.prototype.bind.call( this.logger.log, this.logger );
            }
            return log.apply( this.logger, arguments );
        }
        return undefined;
    }
};


//==============================================================================
/**
 *  @class persistent storage adapter.
 *      Provides an easy interface to object based storage using method chaining.
 *      Allows easy change of the storage engine used (h5's local storage?).
 *  @augments StorageRecursionHelper
 *
 *  @param {String} storageKey : the key the storage engine will place the storage object under
 *  @param {Object} storageDefaults : [optional] initial object to set up storage with
 *
 *  @example
 *  // example of construction and use
 *  HistoryPanel.storage = new PersistanStorage( HistoryPanel.toString(), { visibleItems, {} });
 *  itemView.bind( 'toggleBodyVisibility', function( id, visible ){
 *      if( visible ){
 *          HistoryPanel.storage.get( 'visibleItems' ).set( id, true );
 *      } else {
 *          HistoryPanel.storage.get( 'visibleItems' ).deleteKey( id );
 *      }
 *  });
 *  @constructor
 */
var PersistentStorage = function( storageKey, storageDefaults ){
    if( !storageKey ){
        throw( "PersistentStorage needs storageKey argument" );
    }
    storageDefaults = storageDefaults || {};

    // ~constants for the current engine
    var STORAGE_ENGINE = sessionStorage,
        STORAGE_ENGINE_GETTER = function sessionStorageGet( key ){
            return JSON.parse( this.getItem( key ) );
        },
        STORAGE_ENGINE_SETTER = function sessionStorageSet( key, val ){
            return this.setItem( key, JSON.stringify( val ) );
        },
        STORAGE_ENGINE_KEY_DELETER  = function sessionStorageDel( key ){ return this.removeItem( key ); };

    /** Inner, recursive, private class for method chaining access.
     *  @name StorageRecursionHelper
     *  @constructor
     */
    function StorageRecursionHelper( data, parent ){
        //console.debug( 'new StorageRecursionHelper. data:', data );
        data = data || {};
        parent = parent || null;

        return /** @lends StorageRecursionHelper.prototype */{
            /** get a value from the storage obj named 'key',
             *  if it's an object - return a new StorageRecursionHelper wrapped around it
             *  if it's something simpler - return the value
             *  if this isn't passed a key - return the data at this level of recursion
             */
            get : function( key ){
                //console.debug( this + '.get', key );
                if( key === undefined ){
                    return data;
                } else if( data.hasOwnProperty( key ) ){
                    return ( jQuery.type( data[ key ] ) === 'object' )?
                        ( new StorageRecursionHelper( data[ key ], this ) )
                        :( data[ key ] );
                }
                return undefined;
            },
            /** get the underlying data based on this key */
            // set a value on the current data - then pass up to top to save current entire object in storage
            set : function( key, value ){
                //TODO: add parameterless variation setting the data somehow
                //  ??: difficult bc of obj by ref, closure
                //console.debug( this + '.set', key, value );
                data[ key ] = value;
                this._save();
                return this;
            },
            // remove a key at this level - then save entire (as 'set' above)
            deleteKey : function( key ){
                //console.debug( this + '.deleteKey', key );
                delete data[ key ];
                this._save();
                return this;
            },
            // pass up the recursion chain (see below for base case)
            _save : function(){
                //console.debug( this + '.save', parent );
                return parent._save();
            },
            toString : function(){
                return ( 'StorageRecursionHelper(' + data + ')' );
            }
        };
    }

    //??: more readable to make another class?
    var returnedStorage = {};
        // attempt to get starting data from engine...
        data = STORAGE_ENGINE_GETTER.call( STORAGE_ENGINE, storageKey );

    // ...if that fails, use the defaults (and store them)
    if( data === null || data === undefined ){
        data = jQuery.extend( true, {}, storageDefaults );
        STORAGE_ENGINE_SETTER.call( STORAGE_ENGINE, storageKey, data );
    }

    // the object returned by this constructor will be a modified StorageRecursionHelper
    returnedStorage = new StorageRecursionHelper( data );
    jQuery.extend( returnedStorage, /**  @lends PersistentStorage.prototype */{
        /** The base case for save()'s upward recursion - save everything to storage.
         *  @private
         *  @param {Any} newData data object to save to storage
         */
        _save : function( newData ){
            //console.debug( returnedStorage, '._save:', JSON.stringify( returnedStorage.get() ) );
            return STORAGE_ENGINE_SETTER.call( STORAGE_ENGINE, storageKey, returnedStorage.get() );
        },
        /** Delete function to remove the entire base data object from the storageEngine.
         */
        destroy : function(){
            //console.debug( returnedStorage, '.destroy:' );
            return STORAGE_ENGINE_KEY_DELETER.call( STORAGE_ENGINE, storageKey );
        },
        /** String representation.
         */
        toString : function(){ return 'PersistentStorage(' + storageKey + ')'; }
    });
    
    return returnedStorage;
};