import express from 'express';
import { MongoClient } from 'mongodb';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = 3000;

let collection;

const uri = `mongodb+srv://web:ByiT9WakPCj8izEO@vinskraper.wykjrgz.mongodb.net/`; // Replace with your MongoDB URI


app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static(path.join(__dirname, 'public')));

MongoClient.connect(uri)
  .then(client => {
    const db = client.db('vinskraper'); // Replace with your database name
    collection = db.collection('varer'); // Replace with your collection name

    // Route to display products with pagination
    app.get('/', async (req, res) => {
      try {
        const page = parseInt(req.query.page) || 1; // Get the current page number from query string, default to 1
        const limit = 10; // Number of products to display per page
        const skip = (page - 1) * limit; // Calculate the number of products to skip

        const documents = await collection.find({})
          .skip(skip)
          .limit(limit)
          .toArray();

        const totalDocuments = await collection.countDocuments(); // Get the total number of documents
        const totalPages = Math.ceil(totalDocuments / limit);

        res.render('index', { 
          data: documents,
          currentPage: page,
          totalPages: totalPages
        });
      } catch (err) {
        console.error(err);
        res.status(500).send('Error fetching data from MongoDB');
      }
    });

    app.listen(port, () => {
      console.log(`Server running at http://localhost:${port}`);
    });
  })
  .catch(error => console.error(error));
