var BaseModel=Backbone.RelationalModel.extend({defaults:{name:null,hidden:false},show:function(){this.set("hidden",false)},hide:function(){this.set("hidden",true)},is_visible:function(){return !this.attributes.hidden}});var BaseView=Backbone.View.extend({initialize:function(){this.model.on("change:hidden",this.update_visible,this);this.update_visible()},update_visible:function(){if(this.model.attributes.hidden){this.$el.hide()}else{this.$el.show()}}});var LoggableMixin={logger:null,log:function(){if(this.logger){var a=this.logger.log;if(typeof this.logger.log==="object"){a=Function.prototype.bind.call(this.logger.log,this.logger)}return a.apply(this.logger,arguments)}return undefined}};var PersistentStorage=function(j,g){if(!j){throw ("PersistentStorage needs storageKey argument")}g=g||{};var h=sessionStorage,c=function i(l){return JSON.parse(this.getItem(l))},b=function e(l,m){return this.setItem(l,JSON.stringify(m))},d=function f(l){return this.removeItem(l)};function a(m,l){m=m||{};l=l||null;return{get:function(n){if(n===undefined){return m}else{if(m.hasOwnProperty(n)){return(jQuery.type(m[n])==="object")?(new a(m[n],this)):(m[n])}}return undefined},set:function(n,o){m[n]=o;this._save();return this},deleteKey:function(n){delete m[n];this._save();return this},_save:function(){return l._save()},toString:function(){return("StorageRecursionHelper("+m+")")}}}var k={};data=c.call(h,j);if(data===null||data===undefined){data=jQuery.extend(true,{},g);b.call(h,j,data)}k=new a(data);jQuery.extend(k,{_save:function(l){return b.call(h,j,k.get())},destroy:function(){return d.call(h,j)},toString:function(){return"PersistentStorage("+j+")"}});return k};