require(['gitbook', 'jQuery'], function (gitbook, $) {
  var url = ''
  var insertLogo = function (url) {
    $('.book-summary').children().eq(0).before('<div class="book-logo"><img src=\"' + url + '"</div>')
  }
  gitbook.events.bind('start', function (e, config) {
    url = config['insert-logo']['url']
  })

  gitbook.events.bind("page.change", function() {
    insertLogo(url)
  })
})
