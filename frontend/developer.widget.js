/**
 * Dveloper widget directive
 * Display developer dashboard widget
 */
var widgetDeveloperDirective = function() {

    var widgetDeveloperController = ['$scope', 'developerService', 'raspiotService', function($scope, developerService, raspiotService)
    {
        var self = this;
        self.device = $scope.device;

        //restart cleepos
        self.restartCleepBackend = function() {
            raspiotService.restart(0)
        };
    }];

    return {
        restrict: 'EA',
        templateUrl: 'developer.widget.html',
        replace: true,
        scope: {
            'device': '='
        },
        controller: widgetDeveloperController,
        controllerAs: 'widgetCtl'
    };
};

var RaspIot = angular.module('RaspIot');
RaspIot.directive('widgetDeveloperDirective', [widgetDeveloperDirective]);

