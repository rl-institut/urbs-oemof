-- table description
DROP TABLE IF EXISTS    model_draft.mimo_example CASCADE;
CREATE TABLE            model_draft.mimo_example (
    "id"            serial NOT NULL,
    "model"         text,
    "version"       text,
    "region"        text,
    "variable"      text,
    "value"         double precision,
    "unit"          text,
    "aggregation"   boolean,
    "updated"       timestamp with time zone,
    CONSTRAINT mimo_example_pkey PRIMARY KEY (id) );
