require("dotenv").config();
const express = require("express");
const { MongoClient } = require("mongodb");
const path = require("path");

const app = express();
const port = 3000;

const mongoUri = `mongodb+srv://${process.env.mongodb_username}:${process.env.mongodb_password}@vinskraper.wykjrgz.mongodb.net/?retryWrites=true&w=majority&appName=vinskraper`;
const client = new MongoClient(mongoUri);

app.use(express.static("src"));

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
