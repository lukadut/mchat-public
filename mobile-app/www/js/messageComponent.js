/**
 * Created by admin on 07.01.2017.
 */

angular.module('starter')
  .component('mChatMessage', {
    templateUrl: 'templates/message.html',
    bindings: {message: '<'},
    controller: ['$element', function ($element) {

      this.$postLink = function () {
        var contentElement = $(this.message.content);
        contentElement=this.resolveSpoilers(contentElement);
        this.resolveImages(contentElement);
        $element.find('.content').append(contentElement);
      };

      this.resolveSpoilers = function(contentElement){
        var spoilerButton = contentElement.find('.mChatSpoiler div.quotetitle > b');
        spoilerButton.click(function (elem) {
          $(elem.target).parent().parent().find("div.quotecontent").toggle();
        });
        spoilerButton.addClass('button');
        contentElement.find('div.quotetitle > input').remove();
        return contentElement;
      };

      this.resolveImages= function(contentElement){
        var images = contentElement.find('img[src]');
        images.each(function(iter,elem){
          var src = elem.src;
          if(src.search(localStorage.address)<0) {
            var button = $("<b class='button' " +
              "onclick=\"window.open('" + src + "', '_system', 'location=yes');" +
              " return false;\">Open in browser</b>");
            $(elem).after(button);
          }
        });
      };

    }]
  });
