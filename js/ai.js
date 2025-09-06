var layer_defs = [];
layer_defs.push({type:'input', out_sx:4, out_sy:4, out_depth:16});
var net_params=[256, 2400, 1600, 800, 400, 400, 200, 200, 100, 100, 4];
for(var i= 1;i<net_params.length-1;i++){
    layer_defs.push({type:'fc', num_neurons:net_params[i], activation:'relu'});
}
layer_defs.push({type:'fc', num_neurons:4});

// create a net out of it
var net = new convnetjs.Net();
net.makeLayers(layer_defs);

(function (){
    document.getElementById('ai-info').innerHTML="Downloading model......(about 25M). <br /><strong>NN AI won't work until the model is loaded</strong><div class='progress-container'><div class='progressbar' id='progressbar' style='width: 0%'></div></div>";
    var oReq = new XMLHttpRequest();
    oReq.open("GET", "model.bin", true);
    oReq.responseType = "arraybuffer";
    var updateProgress = function (oEvent) {
    var pb = document.getElementById('progressbar');
    pb.innerHTML=""+ oEvent.loaded+"/25484016";
    var width = 100 * oEvent.loaded/25484016;
    pb.style.width = width + '%'; 
}
    oReq.addEventListener("progress", updateProgress, false);

    oReq.onload = function (oEvent) {
    var arrayBuffer = oReq.response; // Note: not oReq.responseText
    if (arrayBuffer) {
        floatArray = new Float32Array(arrayBuffer);

    var ptr=0|0;
    for(var i=1;i<net_params.length;i++)
    {
        var l = i*2-1;
        for(var x=0;x<net_params[i-1];x++){
            for(var y=0;y<net_params[i];y++){
                    net.layers[l].filters[y].w[x] = floatArray[ptr];
                    ptr++;
            }
        }
        for(var y=0;y<net_params[i];y++){
                    net.layers[l].biases.w[y] = floatArray[ptr];
                        ptr++;
            }
        }
    }
    document.getElementById('ai-info').innerHTML="Model downloaded. enjoy the neural network AI!";
    };
    oReq.send(null);
})();


function AI(grid) {
  this.grid = grid;
  this.v = new convnetjs.Vol(4, 4, 16, 0.0);
}
AI.prototype.make_input = function(){
    this.v.setConst(0.0);
    for(var i=0;i<4;i++){
        for(var j=0;j<4;j++){
            if(this.grid.cells[j][i] !== null){
                var v = this.grid.cells[j][i].value|0;
                var k =0;
                while(v>2){
                    v >>=1;
                    k+=1;
                };
                this.v.w[i*4*16+j*16+k]=1.;
            }
        }
    }

    
}

// performs a search and returns the best move
AI.prototype.getBest = function() {
 //console.log(this.grid);
 this.make_input()
 //console.log(this.v);
 var p = net.forward(this.v).w;
  var m=[0,1,2,3];
  m.sort(function(i,j){return p[j]-p[i]});
  //console.log(p);
  //console.log(m);
  m = m.map(function(x){ return (x+3)%4;})
  return {move:m[0], moves:m};
}


AI.prototype.translate = function(move) {
 return {
    0: 'up',
    1: 'right',
    2: 'down',
    3: 'left'
  }[move];
}
