angular.module('starter')
  .controller("MainController", ["$state", "$ionicHistory", "ChangeView", function ($state, $ionicHistory, ChangeView) {
    (function () {
      if (typeof(localStorage.session) == "undefined" || localStorage.session == "") {
        ChangeView.goToView('login');
      }
      else {
        ChangeView.goToView('mchat');
      }
    })();
  }])
  .controller("LoginController", ["$ionicPopup", "$ionicLoading", "$ionicHistory", "ChangeView", "loginService", function ($ionicPopup, $ionicLoading, $ionicHistory, ChangeView, loginService) {
    var that = this;
    this.address = '';
    this.password = '';
    this.nickname = '';
    this.proxyServer = localStorage.proxyServer || 'http://192.168.1.103:5000';
    this.editProxyServer = false;
    this.loadingShow = function () {
      console.log("$ionicloading: ", $ionicLoading);
      $ionicLoading.show({
        template: "<p>Loading</p><ion-spinner></ion-spinner>"
      })
    };
    this.loadingHide = function () {
      $ionicLoading.hide();
    };

    this.advancedSettings = function () {
      this.editProxyServer = !this.editProxyServer;
    };

    this.getMessageError = function (error) {
      $ionicPopup.alert({
        title: "Error",
        template: error.message || "Cannot connect to proxy server"
      });
      that.loadingHide();
    };

    this.login = function () {
      localStorage.proxyServer = this.proxyServer;
      var data = {
        forum: this.address,
        login: this.nickname,
        password: this.password
      };
      that.loadingShow();
      loginService.login(data,
        function (cookies) {
          localStorage.session = cookies;
          localStorage.address = that.address;
          that.loadingHide();
          ChangeView.goToView('mchat');
        },
        this.getMessageError);
    };
  }])

  .controller("MChatController", ["$http", "$ionicPopup", "$ionicLoading", "ChangeView", "$scope", "messagesService", "$ionicScrollDelegate", "$timeout", function ($http, $ionicPopup, $ionicLoading, ChangeView, $scope, messagesService, $ionicScrollDelegate, $timeout) {
    var that = this;
    this.session = localStorage["session"];
    this.address = localStorage["address"];
    this.lastMessageId = 0;
    this.messages = [];
    this.newMessageText = '';
    this.alertOccurs = false;

    this.scrollToBottom = function () {
      $timeout(function () {
        $ionicScrollDelegate.scrollBottom()
      }, 500);
    };

    this.sendNewMessage = function () {
      messagesService.sendNewMessage(this.newMessageText, function () {
        that.newMessageText = '';
        that.getNewMessages();
      }, that.getMessagesError);
    };

    this.messageProviderLoop = function () {
      console.log("new message loop");
      messagesService.messageProviderLoop(function (newMessages) {
        that.messages = newMessages;
        $scope.$broadcast('scroll.refreshComplete');
      }, function (error) {
        $ionicPopup.alert({
          title: "Error",
          template: error || "Cannot connect to proxy server"
        });
        $scope.$broadcast('scroll.refreshComplete');
      });
    };

    this.getMessagesSuccess = function (newMessages) {
      that.messages = newMessages;
      $scope.$broadcast('scroll.refreshComplete');
    };

    this.getMessagesError = function (error) {
      if(!this.alertOccurs) {
        this.alertOccurs=true;
        $ionicPopup.alert({
          title: "Error",
          template: error.message || "Cannot connect to proxy server"
        }).then(function () {
          that.alertOccurs=false;
          if (error.message == "Invalid session") {
            that.logOut();
          }

        });
      }


      $scope.$broadcast('scroll.refreshComplete');
    };

    this.getNewMessages = function () {
      messagesService.breakMessageProviderLoop();
      this.messageProviderLoop();
      messagesService.getNewMessages(function (newMessages) {
        that.getMessagesSuccess(newMessages);
        that.scrollToBottom();
      }, that.getMessagesError);
    };

    this.getArchiveMessages = function () {
      messagesService.getArchiveMessages(that.getMessagesSuccess, that.getMessagesError);
    };


    this.logOut = function () {
      messagesService.breakMessageProviderLoop();
      localStorage["session"] = "";
      ChangeView.goToView('login');
    };

    $scope.$on("$stateChangeSuccess", function(stateChangeSuccess,route) {
      if(route.name == "mchat") {
        that.session = localStorage["session"];
        that.address = localStorage["address"];
        that.lastMessageId = 0;
        that.messages = [];
        that.newMessageText = '';
        that.getNewMessages();
        messagesService.reset();
      };
    });



  }]);
