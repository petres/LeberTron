var SerialPort = require("serialport").SerialPort
var serialPort = new SerialPort("/dev/tty.usbserial-A9WFF5LH", {
  baudrate: 9600
});


serialPort.on("open", function () {
  console.log('open');
  serialPort.on('data', function(data) {
    console.log('data received: ' + data);
  });
});