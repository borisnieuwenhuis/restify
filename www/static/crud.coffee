define ['jquery'], (JQuery) ->

  create = (params) ->
    defaults =
      formviewelement: "#" + params.model + "-form"
      listviewelement: "#" + params.model + "-listview"
      listviewelement_events: {}
      model_destroy_confirm: false

    $ = JQuery
    params = $.extend defaults, params

    class _Model extends Backbone.Model
       url: () ->
        base = '/admin/restify/' + params.model.toLowerCase()
        if @isNew()
          return base
        return base + '/' + @get("id")

    class ModelList extends Backbone.Collection
      model: _Model
      url: '/admin/restify/' + params.model.toLowerCase() + '/list'

    models = new ModelList()

    class ModelView extends Backbone.View
      initialize: () ->
        if models.get(@model.get("id"))
          @model = models.get(@model.get("id"))
        @model.on 'change', @render
        @model.on 'destroy', @remove
      events: () ->
        _.each params.listviewelement_events, (value, key) ->
          params.listviewelement_events.key = _.bind value, @
        $.extend
          "click .action-edit": "edit"
          "click .action-delete": "delete"
        , params.listviewelement_events
      template: _.template params.listitemtemplate
      tagName: "li"
      delete: () =>
        if params.model_destroy_confirm
          if !confirm params.model_destroy_confirm
            return

        @model.destroy
          wait: true
      edit: () =>
        formview.model = @model
        formview.render()
      remove: () =>
        ($ @el).remove()
      render: () =>
        html = @template @model.toJSON()
        ($ @el).html html
        return @

    class ModelListView extends Backbone.View
      initialize: ->
        models.on 'add', @render
        models.fetch add: true
        @list_container = ($ params.listviewelement)

      el: $ params.listviewelement
      render: (model) =>
        view = new ModelView model: model
        element = view.render().el
        if !@lastId || model.get("id") < @lastId
          @list_container.append element
        else
          @list_container.prepend element
        @lastId = model.get("id")

    modelListView = new ModelListView()

    class ModelFormView extends Backbone.View
      initialize: ->
        @model = new _Model(params.defaults)
      el: params.formviewelement
      reset: () =>
        @model = new _Model(params.defaults)
        @render()
      events:
        "click [type=submit]": "post"
      render: =>
        form = $ @el
        attrs = @model.toJSON()
        _.each _.keys(attrs), (name) ->
          (form.find "[name=" + name + "]").val @model.get(name)
        , @
        @
      post: (event) =>
        event.preventDefault()
        values = _.values ($ @el).serializeArray()
        dict = {}
        _(values).each (element) -> dict[element.name] = element.value
        success =  () ->
          if !models.get @model.get("id")
            models.add @model
          @model = new _Model(params.defaults)
          @render()
        success = _.bind success, @
        @model.save dict,
          success: success
          error: (model, response) ->
            $(".alert-message.error").html response.responseText
            $(".alert-message.error").show()

    formview = new ModelFormView()
    {ModelList: ModelList, ModelListView: ModelListView, formview: formview}


  { create: create }
