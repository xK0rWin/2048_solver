function KeyboardInputManager() {
  this.events = {};
  this.pendingPosition = null; // store last clicked cell
  this.listen();
}

KeyboardInputManager.prototype.on = function (event, callback) {
  if (!this.events[event]) {
    this.events[event] = [];
  }
  this.events[event].push(callback);
};

KeyboardInputManager.prototype.emit = function (event, data) {
  var callbacks = this.events[event];
  if (callbacks) {
    callbacks.forEach(function (callback) {
      callback(data);
    });
  }
};

KeyboardInputManager.prototype.listen = function () {
  var self = this;

  // Movement map
  var map = {
    38: 0, // Up
    39: 1, // Right
    40: 2, // Down
    37: 3, // Left
    75: 0, // K
    76: 1, // L
    74: 2, // J
    72: 3  // H
  };

  // Keys for values
  var placeMap = {
    49: 2,   // '1' -> 2
    50: 4,   // '2' -> 4
    51: 8,   // '3' -> 8
    52: 16,  // '4' -> 16
    53: 32,  // '5' -> 32
    54: 64,  // '6' -> 64
    55: 128, // '7' -> 128
    56: 256, // '8' -> 256
    57: 512, // '9' -> 512
    58: 1024 // '0' -> 1024
  };

  // listen for clicks on cells to set position
  var gridCells = document.querySelectorAll(".grid-container .grid-cell");
  gridCells.forEach(function(cell, index) {
    cell.addEventListener("click", function() {
      // Remove previous selection
      gridCells.forEach(c => c.classList.remove("selected"));

      // Add selected class
      cell.classList.add("selected");

      // Save the selected position
      var x = index % 4; // column
      var y = Math.floor(index / 4); // row
      self.pendingPosition = {x, y};

      console.log("Selected cell:", x, y);
    });
  });



  // listen for placing value
  document.addEventListener("keydown", function (event) {
    var value = placeMap[event.which];
    console.log(value)
    if (value !== undefined && self.pendingPosition) {
      event.preventDefault();
      self.emit("placeTile", {
        x: self.pendingPosition.x,
        y: self.pendingPosition.y,
        value: value
      });
      self.pendingPosition = null; // reset after placing
    }
  });

  // normal move handling
  document.addEventListener("keydown", function (event) {
    var modifiers = event.altKey || event.ctrlKey || event.metaKey || event.shiftKey;
    var mapped    = map[event.which];

    if (!modifiers) {
      if (mapped !== undefined) {
        event.preventDefault();
        var feedbackContainer = document.getElementById("feedback-container");
        feedbackContainer.innerHTML = " ";
        self.emit("move", mapped);
      }
      if (event.which === 32) self.restart.bind(self)(event);
    }
  });

  var retry = document.getElementsByClassName("retry-button")[0];
  retry.addEventListener("click", this.restart.bind(this));

  var hintButton = document.getElementById("hint-button");
  hintButton.addEventListener("click", function(e) {
    e.preventDefault();
    var feedbackContainer  = document.getElementById("feedback-container");
    feedbackContainer.innerHTML = "<img src=img/spinner.gif />";
    self.emit("think");
  });

  var runButton = document.getElementById("run-button");
  runButton.addEventListener("click", function(e) {
    e.preventDefault();
    self.emit("run");
  });

  // swipe handling
  var gestures = [Hammer.DIRECTION_UP, Hammer.DIRECTION_RIGHT,
                  Hammer.DIRECTION_DOWN, Hammer.DIRECTION_LEFT];
  var gameContainer = document.getElementsByClassName("game-container")[0];
  var handler = Hammer(gameContainer, { drag_block_horizontal: true, drag_block_vertical: true });
  handler.on("swipe", function (event) {
    event.gesture.preventDefault();
    mapped = gestures.indexOf(event.gesture.direction);
    if (mapped !== -1) self.emit("move", mapped);
  });
};

KeyboardInputManager.prototype.restart = function (event) {
  event.preventDefault();
  this.emit("restart");
};
