angular.module('starter')
  .factory('ChangeView', ["$state", "$ionicHistory", function ($state, $ionicHistory) {
    return {
      goToView: function (view) {
        $ionicHistory.nextViewOptions({
          disableBack: true,
          disableAnimate: true,
          historyRoot: true
        });
        $ionicHistory.clearCache();
        $ionicHistory.clearHistory();
        $state.go(view);
      }
    }
  }])

  .service("notificationService", ["$timeout","$document", function ($timeout,$document) {
    var that = this;
    this.messagesCounter = 0;
    this.notificationId = 1;
    this.notificationVisible = false;
    this.appInBackground = false;

    this.addMessageNotification = function (newMessagesCount) {
      if(this.appInBackground) {
        this.messagesCounter += newMessagesCount;
        this.notification();
      }
    };

    this.notification = function () {
      if (!this.notificationVisible) {
        this.scheduleNotification();
      }
      else {
        this.updateNotification();
      }
    };

    this.scheduleNotification = function () {
      cordova.plugins.notification.local.schedule({
        id: that.notificationId,
        title: 'MChat ' + localStorage.address,
        text: 'You have ' + that.messagesCounter + ' new message' + (that.messagesCounter>1?'s':'') + '.',
        led: "FFFFFF"
      });
    };

    this.updateNotification = function () {
      cordova.plugins.notification.local.update({
        id: that.notificationId,
        text: 'You have ' + that.messagesCounter + '  new message',
        data: {updated: true}
      });
    };

    this.resetMessagesCounter = function () {
      this.messagesCounter = 0;
    };

    this.onClearNotification = function () {
      $timeout(function () {
        cordova.plugins.notification.local.clear(that.notificationId, function () {
          that.resetMessagesCounter();
        });
        cordova.plugins.notification.local.clearAll(function() {
          that.resetMessagesCounter();
        });

        cordova.plugins.notification.local.on("click", function (notification, state) {
          that.resetMessagesCounter();
        });
      },1000);
    };

    this.addChangeStateListener = function () {
      $document.on('pause',function(){
        that.appInBackground = true;
      });
      $document.on('resume',function(){
        that.appInBackground = false;
      });
    };

    this.onClearNotification();
    this.addChangeStateListener();

  }])

  .service("loginService", ["$http",function ($http) {
    var that = this;
    this.proxyServer = localStorage.proxyServer || 'http://192.168.0.13:5000';


    this.httpRequest = function (url, data) {
      return $http({
        method: 'POST',
        url: that.proxyServer + url,
        data: data
      }).then(function (response) {
        print("login response",response);
        if (response.data.state == "OK") {
          return response.data.cookies;
        }
        else {
          throw new Error(response.data.errors.message);
        }
      })
    };

    this.login = function (data,_successCallback, _errorCallback) {
      this.proxyServer = localStorage.proxyServer;
      that.httpRequest("/login", data)
        .then(function (cookies) {
          return cookies
        })
        .then(function (cookies) {
          _successCallback(cookies);
        })
        .catch(function (error) {
          _errorCallback(error);
        });
    };
  }])

  .service("messagesService", ["$http", "$interval", "notificationService","$window", function ($http, $interval, notificationService,$window) {
    var that = this;
    this.session = localStorage["session"];
    this.address = localStorage["address"];
    this.messages = [];
    this.lastMessageId = 0;
    this.messagesIds = new Set();
    this.messageEventLoop = undefined;
    this.proxyServer = localStorage.proxyServer;

    this.reset = function () {
      this.session = localStorage["session"];
      this.address = localStorage["address"];
      this.messages = [];
      this.lastMessageId = 0;
      this.messagesIds = new Set();
      this.proxyServer = localStorage.proxyServer;
      this.breakMessageProviderLoop();
    };

    this.httpRequest = function (url, data) {
      return $http({
        method: 'POST',
        url: that.proxyServer + url,
        data: data
      }).then(function (response) {
        if (response.data.state == "OK") {
          return response.data.data;
        }
        else {
          throw new Error(response.data.errors.message);
        }
      })
    };

    this.messageProviderLoop = function (_successCallback, _errorCallback) {
      this.breakMessageProviderLoop();
      this.messageEventLoop = $interval(function () {
        that.getNewMessages(_successCallback, _errorCallback);
      }, 5000);
    };

    this.breakMessageProviderLoop = function () {
      if (angular.isDefined(this.messageEventLoop)) {
        console.log("stop message loop");
        $interval.cancel(this.messageEventLoop);
        this.messageEventLoop = undefined;
      }
    };

    this.getNewMessages = function (_successCallback, _errorCallback) {
      var data = {
        forum: that.address,
        cookies: JSON.parse(that.session),
        messageid: that.lastMessageId
      };

      that.httpRequest("/mchatmessages", data)
        .then(function (messages) {
          return messages
        })
        .then(function (messages) {
          if (messages.length > 0) {
            notificationService.addMessageNotification(messages.length);
            navigator.vibrate([100,100,100]);
          }
          that.messages = that.concatMessages(messages);
          return that.messages;
        })
        .then(function (messages) {
          _successCallback(messages);
        })
        .catch(function (error) {
          _errorCallback(error);
        });
    };

    this.getArchiveMessages = function (_successCallback, _errorCallback) {
      var data = {
        forum: that.address,
        cookies: JSON.parse(that.session),
        readmessages: that.messages.length
      };

      that.httpRequest("/mchatarchive", data)
        .then(function (messages) {
          return messages
        })
        .then(function (messages) {
          that.messages = that.concatMessages(messages);
          return that.messages;

        })
        .then(function (messages) {
          _successCallback(messages);
        })
        .catch(function (error) {
          _errorCallback(error);
        });
    };

    this.sendNewMessage = function (newMessageText, _successCallback, _errorCallback) {
      var data = {
        forum: that.address,
        cookies: JSON.parse(that.session),
        message: newMessageText
      };
      that.httpRequest("/mchatadd", data)
        .then(function () {
          _successCallback();
        })
        .catch(function (error) {
          _errorCallback(error);
        });

    };

    this.concatMessages = function (newMessages) {
      if (newMessages.length == 0) {
        return that.messages;
      }
      newMessages.forEach(function (newMessage) {
        if (!that.messagesIds.has(newMessage.messageid)) {
          that.messages.push(newMessage);
          that.messagesIds.add(newMessage.messageid);
        }
      });
      that.messages = that.messages.sort(function (a, b) {
        return a.messageid - b.messageid
      });
      that.lastMessageId = that.messages[that.messages.length - 1].messageid;
      return that.messages;

    };

  }]);
