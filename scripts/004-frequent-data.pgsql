--
-- Table of info we think might be linked to Event
--

CREATE TABLE frequencies
(
    activity_type   TEXT,
    common_titles   TEXT[],
    common_labels   TEXT,
    avg_desc_length INT      
);