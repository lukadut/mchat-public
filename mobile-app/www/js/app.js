angular.module('starter', ['ionic','ui.router'])
  .run(function ($ionicPlatform) {
    $ionicPlatform.ready(function () {
      if (window.cordova && window.cordova.plugins && window.cordova.plugins.Keyboard) {
        cordova.plugins.Keyboard.hideKeyboardAccessoryBar(true);
        cordova.plugins.Keyboard.disableScroll(true);

      }
      if (window.StatusBar) {
        StatusBar.styleDefault();
      }
    });
  })

  .config(function ($stateProvider, $urlRouterProvider) {
    $stateProvider
      .state('main',{
        url:'/',
        templateUrl: 'templates/main.html'
      })

      .state('login', {
        url: '/login',
        templateUrl: 'templates/login.html'


      })
      .state('mchat', {
        url: '/mchat',
        templateUrl: 'templates/mchat.html'


      });

    $urlRouterProvider.otherwise('/');

  });
