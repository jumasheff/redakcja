(function($) 
{		
	var noop = function() { };
	
	$.wiki = {
		perspectives: {},
		cls: {}		
	};
	
	$.wiki.activePerspective = function() { 
		return this.perspectives[$("#tabs li.active").attr('id')];
	};
	
	$.wiki.exitContext = function() {
		var ap = this.activePerspective();
		if(ap) ap.onExit();
		return ap;	
	};
	
	$.wiki.enterContext = function(ap) {
		if(ap) ap.onEnter();				
	};
	
	$.wiki.isDirty = function() {
		var ap = this.activePerspective();
		return (!!CurrentDocument && CurrentDocument.has_local_changes) || ap.dirty(); 
	};
	
	$.wiki.newTab = function(doc, title, klass) {
		var base_id = 'id' + Math.floor(Math.random()* 5000000000);
		var id = (''+klass)+'_' + base_id;
		var $tab = $('<li id="'+id+'" data-ui-related="'+base_id+'" data-ui-jsclass="'+klass+'" >'
				+ title + '<img src="/static/icons/close.png" class="tabclose"></li>');
		var $view = $('<div class="editor '+klass+'" id="'+base_id+'"> </div>');		
		
		this.perspectives[id] = new $.wiki[klass]({
			doc: doc,
			id: id,
			base_id: base_id,
		});		
		
		$('#tabs').append($tab);					
		$view.hide().appendTo('#editor');			
		return {
			tab: $tab[0],
			view: $view[0],
		};							
	};
	
	$.wiki.initTab = function(options) {
		var klass = $(options.tab).attr('data-ui-jsclass');
		
		return new $.wiki[klass]({
			doc: options.doc,
			id: $(options.tab).attr('id'),
			callback: function() {
				$.wiki.perspectives[this.perspective_id] = this;
				if(options.callback)
					options.callback.call(this);				
			}			
		});
	};
	
	$.wiki.perspectiveForTab = function(tab) { // element or id
		return this.perspectives[ $(tab).attr('id')];
	}
	
	$.wiki.switchToTab = function(tab){
		var self = this;
		var $tab = $(tab);
		
		if($tab.length != 1) 
			$tab = $(DEFAULT_PERSPECTIVE);
		
		var $old = $('#tabs li').filter('.active');
				
		$old.each(function(){
			$(this).removeClass('active');
			$('#' + $(this).attr('data-ui-related')).hide();
			self.perspectives[$(this).attr('id')].onExit();
		});
		
		/* show new */
		$tab.addClass('active');
		$('#' + $tab.attr('data-ui-related')).show();
		
		console.log($tab);
		console.log($.wiki.perspectives);
		
		$.wiki.perspectives[$tab.attr('id')].onEnter();
	};
	
	/*
	 * Basic perspective.
	 */
	$.wiki.Perspective = function(options) {
		if(!options) return;
		
		this.doc = options.doc;
		if (options.id) {
			this.perspective_id = options.id;
		}
		else {
			this.perspective_id = '';
		}
				
		if(options.callback)
			options.callback.call(this);
	};
	
	$.wiki.Perspective.prototype.toString = function() {
		return this.perspective_id;
	};
	
	$.wiki.Perspective.prototype.dirty = function() {
		return true;
	};
	
	$.wiki.Perspective.prototype.onEnter = function () {
		// called when perspective in initialized
		if (this.perspective_id) {
			document.location.hash = '#' + this.perspective_id;
		}
			 
		console.log(document.location.hash);
	};
	
	$.wiki.Perspective.prototype.onExit = function () {
		// called when user switches to another perspective 
		document.location.hash = '';
	};	 
	
	$.wiki.Perspective.prototype.destroy = function() {
		// pass		
	};
	
	$.wiki.Perspective.prototype.freezeState = function () {
		// free UI state (don't store data here)
	};
	
	$.wiki.Perspective.prototype.unfreezeState = function (frozenState) {
		// restore UI state
	};
	
	/*
	 * Stub rendering (used in generating history)
	 */
	$.wiki.renderStub = function($container, $stub, data) 
	{
		var $elem = $stub.clone();
		$elem.removeClass('row-stub');
		$container.append($elem);
	
		$('*[data-stub-value]', $elem).each(function() {
			var $this = $(this);
			var field = $this.attr('data-stub-value');
			var value = data[field];
		
			if(value === null || value === undefined) return;
			 
			if(!$this.attr('data-stub-target')) {
				$this.text(value);			
			} 		
			else {
				$this.attr($this.attr('data-stub-target'), value);
				$this.removeAttr('data-stub-target');
				$this.removeAttr('data-stub-value');			
			}		
		});
	
		$elem.show();
		return $elem;						
	};
	
	/*
	 * Dialogs
	 */
	function GenericDialog(element) {
		if(!element) return;
		
		var self = this;
				
		self.$elem = $(element);
		
		if(!self.$elem.attr('data-ui-initialized')) {
			console.log("Initializing dialog", this);
			self.initialize();
			self.$elem.attr('data-ui-initialized', true);			
		}
		 
		self.show();				
	};
	
	GenericDialog.prototype = {
	
		/*
	 	* Steps to follow when the dialog in first loaded on page.
	 	*/
		initialize: function(){
			var self = this;
			
			/* bind buttons */
			$('button[data-ui-action]', self.$elem).click(function(event) {
				event.preventDefault();
				
				var action = $(this).attr('data-ui-action');
				console.log("Button pressed, action: ", action);
				 
				try {
					self[action + "Action"].call(self);
				} catch(e) {
					console.log("Action failed:", e);
					// always hide on cancel
					if(action == 'cancel')
						self.hide();					
				}								
			});			
		},
		
		/* 
		 * Prepare dialog for user. Clear any unnessary data.
	 	*/
		show: function() {
			$.blockUI({
				message: this.$elem,
				css: {
					'top': '25%',
					'left': '25%',
					'width': '50%'
				}
			});
		},
		
		hide: function(){
			$.unblockUI();
		},
		
		cancelAction: function() {
			this.hide();			
		},
		
		doneAction: function() {
			this.hide();
		},
		
		clearForm: function() {
			$("*[data-ui-error-for]", this.$elem).text('');
		},
		
		reportErrors: function(errors) {
			var global = $("*[data-ui-error-for='__all__']", this.$elem);
			var unassigned = [];
			
			for (var field_name in errors) 
			{				
				var span = $("*[data-ui-error-for='"+field_name+"']", this.$elem);
				
				if(!span.length) {
					unassigned.push(field_name);
					continue;
				}
				
				span.text(errors[field_name].join(' '));	
			}
			
			if(unassigned.length > 0)
				global.text( global.text() + 'W formularzu wystąpiły błędy');
		}	
	};	 
	
	$.wiki.cls.GenericDialog = GenericDialog;  
	 
	$.wiki.showDialog = function(selector) {
	 	var elem = $(selector);
		
		if(elem.length != 1) {
			console.log("Failed to show dialog:", selector, elem);
			return false;			
		}
		
		try {	
		    var klass = elem.attr('data-ui-jsclass') 
			return new $.wiki.cls[klass](elem);						
		} catch(e) {
			console.log("Failed to show dialog", selector, klass, e);
			return false;
		}		 
	};
	
})(jQuery);