// Any element with `js-header-toggle` class will show/hide the element id referenced by href when
// it's clicked.
(function () {
    "use strict"

    // header navigation toggle
    if ('addEventListener' in document) {
        document.addEventListener(
            'DOMContentLoaded',

            // This function from https://github.com/alphagov/govuk_template/blob/master/source/assets/javascripts/core.js
            function () {
                if (document.querySelectorAll && document.addEventListener) {
                    var els = document.querySelectorAll('.js-header-toggle'),
                        i, _i;
                    for (i = 0, _i = els.length; i < _i; i++) {
                        els[i].addEventListener('click', function (e) {
                            e.preventDefault();
                            var target = document.getElementById(this.getAttribute('href').substr(1)),
                                targetClass = target.getAttribute('class') || '',
                                sourceClass = this.getAttribute('class') || '';

                            if (targetClass.indexOf('js-visible') !== -1) {
                                target.setAttribute('class', targetClass.replace(/(^|\s)js-visible(\s|$)/, ''));
                            } else {
                                target.setAttribute('class', targetClass + " js-visible");
                            }
                            if (sourceClass.indexOf('js-visible') !== -1) {
                                this.setAttribute('class', sourceClass.replace(/(^|\s)js-visible(\s|$)/, ''));
                            } else {
                                this.setAttribute('class', sourceClass + " js-visible");
                            }
                            this.setAttribute('aria-expanded', this.getAttribute('aria-expanded') !== "true");
                            target.setAttribute('aria-hidden', target.getAttribute('aria-hidden') === "false");
                        });
                    }
                }
            });
    }
}).call(this);
