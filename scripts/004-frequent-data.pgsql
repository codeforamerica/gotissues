--
-- Table of info we think might be linked to Event
--

CREATE TABLE activity_summary
(
    activity_type   TEXT,
    common_titles   TEXT[],
    common_labels   TEXT[],
    count INT      
);