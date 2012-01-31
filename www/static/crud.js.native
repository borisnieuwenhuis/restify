init = function (classname, listviewelement, listitemtemplate, formviewelement) {

    var _Model = Backbone.Model.extend({
        url: '/restify/' + classname,
    });

    ModelList = Backbone.Collection.extend({
        model: _Model,
        url: '/restify/' + classname + '/list'
    });

    models = new ModelList()
    models.fetch({async: false});

    var ModelListView = Backbone.View.extend({
        el: $(listviewelement),
        initialize: function() {
            this.render();
        },
        template: _.template(listitemtemplate),
        render: function() {
            this.el.html("");
            models.each(function(model) {
                this.el.append(this.template(model.toJSON()));
            }, this);
        }
    });

    modelListView = new ModelListView;

    var modelFormView = Backbone.View.extend({
        initialize: function() {
            this.model = new _Model
        },
        el: $(formviewelement),
        events: {
            "click [type=submit]": "post"
        },
        render: function() {
            this.el.find("[name=name]").val(this.model.name);
            this.el.find("[name=lastname]").val(this.model.lastname);
        },
        post: function(event) {
            event.preventDefault();
            var values = _.values(this.el.serializeArray());
            var dict = {};
            _(values).each(function(element) {dict[element.name] = element.value});
            this.model.save(dict, {
                error: function(model, response) {
                    $(".alert-message.error").html(response.responseText);
                    $(".alert-message.error").show();
                }
            });
            models.add(this.model);
            modelListView.render();
            this.render();
            this.model = new _Model
        }
    });

    view = new modelFormView;
}