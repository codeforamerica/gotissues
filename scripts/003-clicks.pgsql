--
-- Table of click timestamps
--

CREATE TABLE clicks
(
    id          INT PRIMARY KEY,
    timestamp   TIMESTAMP,
    issue_id    INT REFERENCES issues(id)
);
