/*
 Navicat Premium Data Transfer

 Source Server         : LightnovelSpider
 Source Server Type    : SQLite
 Source Server Version : 3030001
 Source Schema         : main

 Target Server Type    : SQLite
 Target Server Version : 3030001
 File Encoding         : 65001

 Date: 28/11/2021 22:18:32
*/

PRAGMA foreign_keys = false;

-- ----------------------------
-- Table structure for bookwalker_global
-- ----------------------------
DROP TABLE IF EXISTS "bookwalker_global";
CREATE TABLE "bookwalker_global" (
  "pid" INTEGER NOT NULL,
  "title" TEXT NOT NULL,
  "author" TEXT,
  "illustrator" TEXT,
  "publisher" TEXT,
  "release_year" integer,
  "release_month" integer,
  "release_day" integer,
  "description" TEXT,
  "submit" integer DEFAULT 0,
  PRIMARY KEY ("pid")
);

-- ----------------------------
-- Table structure for bookwalker_jp
-- ----------------------------
DROP TABLE IF EXISTS "bookwalker_jp";
CREATE TABLE "bookwalker_jp" (
  "pid" INTEGER NOT NULL,
  "title" TEXT NOT NULL,
  "author" TEXT,
  "illustrator" TEXT,
  "publisher" TEXT,
  "release_year" integer,
  "release_month" integer,
  "release_day" integer,
  "description" TEXT,
  "submit" integer DEFAULT 0,
  PRIMARY KEY ("pid")
);

-- ----------------------------
-- Table structure for bookwalker_tw
-- ----------------------------
DROP TABLE IF EXISTS "bookwalker_tw";
CREATE TABLE "bookwalker_tw" (
  "pid" INTEGER NOT NULL,
  "title" TEXT NOT NULL,
  "author" TEXT,
  "illustrator" TEXT,
  "translator" TEXT,
  "publisher" TEXT,
  "release_year" integer,
  "release_month" integer,
  "release_day" integer,
  "isbn" integer,
  "description" TEXT,
  "submit" integer DEFAULT 0,
  PRIMARY KEY ("pid")
);

-- ----------------------------
-- Table structure for kadokawa_cn
-- ----------------------------
DROP TABLE IF EXISTS "kadokawa_cn";
CREATE TABLE "kadokawa_cn" (
  "pid" integer NOT NULL,
  "title" TEXT NOT NULL,
  "author" TEXT,
  "illustrator" TEXT,
  "publisher" TEXT,
  "release_year" integer,
  "release_month" integer,
  "isbn" integer,
  "description" TEXT,
  "submit" integer DEFAULT 0,
  PRIMARY KEY ("pid")
);

-- ----------------------------
-- Table structure for libi
-- ----------------------------
DROP TABLE IF EXISTS "libi";
CREATE TABLE "libi" (
  "bid" INTEGER NOT NULL,
  "title" TEXT NOT NULL,
  "author" TEXT,
  "volume" TEXT,
  "cid" INTEGER NOT NULL ON CONFLICT IGNORE,
  "chapter" TEXT NOT NULL,
  "content" TEXT,
  "submit" integer DEFAULT 0,
  PRIMARY KEY ("cid")
);

-- ----------------------------
-- Table structure for wenku8
-- ----------------------------
DROP TABLE IF EXISTS "wenku8";
CREATE TABLE "wenku8" (
  "aid" INTEGER NOT NULL,
  "title" TEXT NOT NULL,
  "author" TEXT,
  "cid" INTEGER NOT NULL,
  "subtitle" TEXT NOT NULL,
  "content" TEXT,
  "submit" integer DEFAULT 0,
  PRIMARY KEY ("cid")
);

PRAGMA foreign_keys = true;
