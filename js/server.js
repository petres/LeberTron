var app = require('http').createServer(handler),
    io = require('socket.io').listen(app),
    fs = require('fs');

// creating the server 
app.listen(8888);

var sp = require("serialport");
var SerialPort = sp.SerialPort;

var serialPort = new SerialPort("/dev/tty.usbserial-A9WFF5LH", {
    baudrate: 9600,
    parser: sp.parsers.readline("\n")
});


// on server started we can load our client.html page
function handler(req, res) {
    fs.readFile(__dirname + '/client.html', function(err, data) {
        if (err) {
            console.log(err);
            res.writeHead(500);
            return res.end('Error loading client.html');
        }
        res.writeHead(200);
        res.end(data);
    });
}

// creating a new websocket to keep the content updated without any AJAX request
io.sockets.on('connection', function(socket) {
        // serialPort.on("open", function () {
    console.log('open');
    serialPort.on('data', function(data) {
        console.log('data received: ' + data);
        msg = JSON.stringify({dis : data})
        // send the new data to the client
        socket.volatile.emit('notification', msg);
    });
        // });
});