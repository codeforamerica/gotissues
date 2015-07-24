--
-- Table of issues we've pinged on Github
--

CREATE TABLE pinged_issues
(
  html_url     TEXT,
  status       TEXT,
  date_pinged  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);