function AndTagFilter() {
    return function (gameList, targetTag) {

        // タグが未指定のときは全部表示
        var enabledCount = 0;
        angular.forEach(targetTag, function(tag) {
            if (tag.checked == true){
                enabledCount += 1;
            }
        });

        if (enabledCount == 0) {
            return gameList;
        }

        var out = [];

        angular.forEach(gameList, function (game) {
            var tagCounter = 0;
            var checkCounter = 0;
            angular.forEach(targetTag, function (tag) {
                if (tag.checked) {
                    checkCounter += 1;
                    
                    if (game.tags && game.tags.indexOf(tag.name) != -1) {
                        tagCounter += 1;
                    }
                }
            });
            if (tagCounter == checkCounter){
                out.push(game);
            }
        });

        return out;
    };
}

angular.module('myApp', ['angular-loading-bar'])
    .controller('myController', ['$scope', '$http', function($scope, $http, cfpLoadingBar) {

        $scope.onclick = function() {
            $http({
                method : 'GET',
                url : 'http://www.dos1506.top/steam/api?profile=' + $scope.profile
            }).then(function(res) {
                $scope.games = res.data;

                // orderByを正しく動作させるために文字列->数値変換
                // 未プレイの場合は0にする
                angular.forEach($scope.games, function(value){
                    value.hoursOnRecord = parseFloat(value.hoursOnRecord);
                    if(isNaN(value.hoursOnRecord)){
                        value.hoursOnRecord = 0;
                    }
                });

                var allTag = [];
                angular.forEach($scope.games, function(game){
                    angular.forEach(game.tags, function(tag){
                        if (!allTag.includes(tag) && tag){
                            allTag.push(tag);
                        }
                    });
                });

                $scope.tagArray = [];
                angular.forEach(allTag, function(tag){
                    $scope.tagArray.push({"name": tag, "checked": false});
                });
            })
        };
    }])
    .filter('andTagFilter', AndTagFilter);
