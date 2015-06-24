--
-- Table of clicked Github Issue data
--

CREATE TABLE issues
(
    -- Id is the Github Issue Id
    id          INT PRIMARY KEY,
    
    -- We hand pick useful attibutes from the full Github API
    html_url    TEXT,
    title       TEXT,
    body        TEXT,
    labels      JSON,
    state       TEXT,
    comments    INT,
    created_at  TIMESTAMP,
    closed_at   TIMESTAMP,
    closed_by   JSON,

    -- Google Analytics Data
    clicks      INT,
    views       INT
);
