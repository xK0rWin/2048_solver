function GameManager(size, InputManager, Actuator) {
  this.size         = size; // Size of the grid
  this.inputManager = new InputManager;
  this.actuator     = new Actuator;

  this.running      = false;

  this.inputManager.on("move", this.move.bind(this));
  this.inputManager.on("restart", this.restart.bind(this));

  this.inputManager.on('think', function() {
    var best = this.ai.getBest();
    if(best && best.move !== undefined) {
      this.actuator.showHint(best.move);  // show hint
      this.move(best.move);               // execute the move
    }
  }.bind(this));


  this.inputManager.on('run', function() {
    if (this.running) {
      this.running = false;
      this.actuator.setRunButton('Auto-run');
    } else {
      this.running = true;
      this.run()
      this.actuator.setRunButton('Stop');
    }
  }.bind(this));

  this.inputManager.on("placeTile", function(data) {
    console.log(data)
    this.placeTile(data.x, data.y, data.value);
  }.bind(this));


  this.setup();
}

// Restart the game
GameManager.prototype.restart = function () {
  this.actuator.restart();
  this.running = false;
  this.actuator.setRunButton('Auto-run');
  this.setup();
};

// Set up the game
GameManager.prototype.setup = function () {
  this.grid         = new Grid(this.size);
  //this.grid.addStartTiles();

  this.ai           = new AI(this.grid);

  this.score        = 0;
  this.over         = false;
  this.won          = false;

  // Update the actuator
  this.actuate();
};


// Sends the updated grid to the actuator
GameManager.prototype.actuate = function () {
  this.actuator.actuate(this.grid, {
    score: this.score,
    over:  this.over,
    won:   this.won
  });
};

// makes a given move and updates state
GameManager.prototype.move = function(direction) {
  var result = this.grid.move(direction);
  if(!result.moved)
      return false;
  
  this.score += result.score;

  if (!result.won) {
    if (result.moved) {
      //this.grid.computerMove();
    }
  } else {
    this.won = true;
  }

  //console.log(this.grid.valueSum());

  if (!this.grid.movesAvailable()) {
    this.over = true; // Game over!
  }

  this.actuate();
  return true;
}

// moves continuously until game is over
GameManager.prototype.run = function() {
  var best = this.ai.getBest();
  for(var i=0;i<4;i++){
    var m=best.moves[i];
    if(this.move(m)) break;
  }
  var timeout = animationDelay;
  if (this.running && !this.over && !this.won) {
    var self = this;
    setTimeout(function(){
      self.run();
    }, timeout);
  }
}

// Place a tile manually at given (x,y) with a given value
GameManager.prototype.placeTile = function (x, y, value) {
  if (!this.grid.withinBounds({ x: x, y: y })) {
    console.warn("Position out of bounds");
    return false;
  }
  if (this.grid.cellOccupied({ x: x, y: y })) {
    console.warn("Cell already occupied");
    return false;
  }

  var tile = new Tile({ x: x, y: y }, value);
  this.grid.insertTile(tile);
  this.actuate();
  var gridCells = document.querySelectorAll(".grid-container .grid-cell");
  gridCells.forEach(c => c.classList.remove("selected"));
  
  return true;
};

