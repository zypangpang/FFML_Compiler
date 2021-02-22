CREATE TEMPORARY VIEW `event_1` AS ( SELECT * FROM transfer WHERE channel='ONL' )
CREATE TEMPORARY VIEW `procedure_1` AS ( SELECT id,rowtime,BADACCOUNT(dest_accountnumber) as isbad FROM event_1 )
CREATE TEMPORARY VIEW `comparison_1` AS ( SELECT id, rowtime FROM procedure_1 WHERE `isbad` = TRUE )
CREATE TEMPORARY VIEW `condition_1` AS ( SELECT * FROM event_1 WHERE id IN ( SELECT id FROM comparison_1 ) )
CREATE TEMPORARY VIEW `action_1` AS ( SELECT `id`,`accountnumber`,sourcetime,PROCTIME() AS resulttime FROM condition_1 )
INSERT INTO alert SELECT * FROM action_1
~
~