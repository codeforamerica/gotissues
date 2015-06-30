--
-- Table of clicked Github Issue data
--

CREATE TABLE activity
(

    clicked_at        TIMESTAMP,

    -- Issue id is the issue that the click is related to
    issue_id          INT PRIMARY KEY,
    nearby_events     TEXT[],
    fork_count        INT,
    watch_count       INT,
    push_count        INT,
    issue_count       INT,
    pr_count          INT

);
