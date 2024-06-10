const { Pool } = require('pg');
const {hash} = require ('bcrypt') ;
require('dotenv').config();

const pool = new Pool({
  user: process.env.POSTGRES_USER,
  // Use 'localhost' if the database is on the same machine
  host: process.env.POSTGRES_HOST || 'localhost',
  database: process.env.POSTGRES_DATABASE,
  password: process.env.POSTGRES_PASSWORD,
  port: process.env.POSTGRES_PORT,
});


const {
  invoices,
  customers,
  revenue,
  users
} = require('../app/lib/placeholder-data.js');

async function seedUsers(client) {
  try {
    await client.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');

    // Create "users" table
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
      );
    `);

    console.log(`Created "users" table`);

    // Insert users (with password hashing)
    for (const user of users) {
      const hashedPassword = await hash(user.password, 10);
      await client.query(`
        INSERT INTO users (id, name, email, password)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO NOTHING;
      `, [user.id, user.name, user.email, hashedPassword]);
    }

    console.log(`Seeded ${users.length} users`);

  } catch (error) {
    console.error('Error seeding users:', error);
    throw error;
  }
}

async function seedInvoices(client) {
  try {
    await client.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'); // Use client.query instead of client.sql

    // Create "invoices" table
    await client.query(`
      CREATE TABLE IF NOT EXISTS invoices (
        id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
        customer_id UUID NOT NULL,
        amount INT NOT NULL,
        status VARCHAR(255) NOT NULL,
        date DATE NOT NULL
      );
    `);

    console.log(`Created "invoices" table`);

    // Insert invoices
    for (const invoice of invoices) {
      await client.query(`
        INSERT INTO invoices (customer_id, amount, status, date)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO NOTHING;
      `, [invoice.customer_id, invoice.amount, invoice.status, invoice.date]);
    }

    console.log(`Seeded ${invoices.length} invoices`);

  } catch (error) {
    console.error('Error seeding invoices:', error);
    throw error; // Re-throw error for main to catch
  }
}

async function seedCustomers(client) {
  try {
    await client.query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"');

    // Create "customers" table
    await client.query(`
      CREATE TABLE IF NOT EXISTS customers (
        id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        image_url VARCHAR(255) NOT NULL
      );
    `);

    console.log(`Created "customers" table`);

    // Insert customers
    for (const customer of customers) {
      await client.query(`
        INSERT INTO customers (id, name, email, image_url)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (id) DO NOTHING;
      `, [customer.id, customer.name, customer.email, customer.image_url]);
    }

    console.log(`Seeded ${customers.length} customers`);

  } catch (error) {
    console.error('Error seeding customers:', error);
    throw error; // Re-throw error for main to catch
  }
}

async function seedRevenue(client) {
  try {
    // Create "revenue" table
    await client.query(`
      CREATE TABLE IF NOT EXISTS revenue (
        month VARCHAR(4) NOT NULL UNIQUE,
        revenue INT NOT NULL
      );
    `);

    console.log(`Created "revenue" table`);

    // Insert revenue
    for (const rev of revenue) {
      await client.query(`
        INSERT INTO revenue (month, revenue)
        VALUES ($1, $2)
        ON CONFLICT (month) DO NOTHING;
      `, [rev.month, rev.revenue]);
    }

    console.log(`Seeded ${revenue.length} revenue entries`);

  } catch (error) {
    console.error('Error seeding revenue:', error);
    throw error; // Re-throw error for main to catch
  }
}

async function main() {
  const client = await pool.connect();
  try {
    await seedUsers(client);
    await seedCustomers(client);
    await seedInvoices(client);
    await seedRevenue(client);
    console.log("Database seeding complete!");
  } catch (error) {
    console.error('Error seeding the database:', error);
  } finally {
    client.release();
    await pool.end();
  }
}

main()
