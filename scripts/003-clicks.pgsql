--
-- Table of click timestamps
--

CREATE TABLE clicks
(
    id          SERIAL PRIMARY KEY,
    timestamp   TIMESTAMP,
    readable_date TEXT,
    issue_url   TEXT
);
