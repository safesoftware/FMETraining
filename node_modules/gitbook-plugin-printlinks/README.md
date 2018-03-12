printlinks
==========
Add footnotes or a glossary of links for ebook/pdf versions of your gitbook

[![NPM](https://nodei.co/npm/gitbook-plugin-printlinks.png?downloads=true&downloadRank=true&stars=true)](https://nodei.co/npm/gitbook-plugin-printlinks)
[![NPM](https://nodei.co/npm-dl/gitbook-plugin-printlinks.png?height=3)](https://nodei.co/npm/gitbook-plugin-printlinks)

Usage
-----

Just add the plugin on the plugins array of your book.json file:

```json
{
  "plugins": ["printlinks"]
}
```

To show external links in a glossary, add this to the `pluginsConfig` field in your `book.json`:
```json
"printlinks": {
  "externalLinksAreReferences": true
}
```


and then add a block like this on a page in your book, where you want the glossary to be:
```
{% printlinks %}
# External References

Here all external resources are listed, that are referenced with in this book.
{% endprintlinks %}
```

To do
-----

* Show alert for duplicated links
* Sort footnotes and footnotes ids by their position on the text. Current ones
  using text ids has preference
