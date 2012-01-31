window.init = (classname, listviewelement, listitemtemplate, formviewelement) ->

class _Model extends Backbone.Model
  url: '/restify' + classname

class ModelList extends Backbone.Collection
  model: _Model
  url: '/restify' + classname + 'list'

models = new ModelList()
models.fetch async: false

class ModelListView extends Backbone.View
  initialize: ->
    @render()
  el: $(listviewelement)
  render: =>
    $(@el).html("")
    models.each (model) =>
      @el.append @template model.toJSON()

modelListView = new ModelListView()

class modelFormView extends Backbone.View
  initialize: =>
    @model = new _Model()
  el: $(formviewelement)
  events:
    "click [type=submit]": "post"
  render: =>
    (@el.find "[name=name]").val(@model.name)
    (@el.find "[name=lastname]").val(@model.lastname)
    @
  post: (event) =>
    event.preventDefault()
    values = _.values @el.serializeArray()
    dict = {}
    _(values).each (element) -> dict[element.name] = element.value
    @model.save dict,
     error: (model, response) ->
      $(".alert-message.error").html response.responseText
      $(".alert-message.error").show()
    models.add @model
    modelListView.render()
    @render()
    @model = new _Model()

view = new modelFormView()

