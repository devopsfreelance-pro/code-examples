const express = require('express');
const _ = require('lodash');

const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.json({ status: 'ok', merged: _.merge({}, { demo: true }) });
});

app.listen(port, () => {
  console.log(`demo-scan-app escuchando en puerto ${port}`);
});
