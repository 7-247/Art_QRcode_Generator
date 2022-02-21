
    /*初始化*/
    window.onload = function () {
        RandomXiaoxingxing(600);
        RandomXingxing(0);
    };
  
    window.onresize = function () {
        RandomXingxing(240);
    };
  
    /*随机生成小行星*/
    function RandomXiaoxingxing(num) {
        var xiaoxingxing = '';
        for (let i = num; i >= 0; i--) {
            /*X轴坐标*/
            let j = Math.round(Math.random() * 360) - 180;
            /*Y轴坐标*/
            let k = Math.round(Math.random() * 360) - 180;
            /*随机透明度*/
            let l = Math.random() * 0.5;
            /*环形判断*/
            if (j * j + k * k <= 160 * 160) {
                xiaoxingxing += (j + 'px ' + k + 'px 0 -139px rgba(255,255,255,' + l + '),')
            }
        }
        /*截掉最后多余的逗号*/
        xiaoxingxing = xiaoxingxing.substr(0, xiaoxingxing.length - 1);
        /*添加到页面*/
        document.getElementsByClassName('xiaoxingxing')[0].style.boxShadow = xiaoxingxing;
    }