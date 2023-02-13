ALTER TABLE
  segment_events
ADD
  COLUMN source_device TEXT;

UPDATE
  segment_events
SET
  source_device = 'CVP';

ALTER TABLE
  intersection_events
ADD
  COLUMN source_device TEXT;

UPDATE
  intersection_events
SET
  source_device = 'CVP';