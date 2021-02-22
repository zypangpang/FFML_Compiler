CREATE TEMPORARY VIEW `event_1` AS ( SELECT * FROM transfer WHERE channel='ONL' )
CREATE TEMPORARY VIEW `procedure_1` AS ( SELECT id,rowtime, USUALIP(accountnumber) as usualip FROM event_1 )
CREATE TEMPORARY VIEW `comparison_1` AS ( SELECT transfer.id AS id, transfer.rowtime AS rowtime FROM procedure_1, transfer WHERE procedure_1.id=transfer.id procedure_1.`usualip` <> transfer.`ip` )
CREATE TEMPORARY VIEW `condition_1` AS ( SELECT * FROM event_1 WHERE id IN ( SELECT id FROM comparison_1 ) )
CREATE TEMPORARY VIEW `procedure_2` AS ( SELECT id,rowtime, USUALDEVICEID(accountnumber) as usualdid FROM condition_1 )
CREATE TEMPORARY VIEW `comparison_2` AS ( SELECT transfer.id AS id, transfer.rowtime AS rowtime FROM procedure_2, transfer WHERE procedure_2.id=transfer.id procedure_2.`usualdid` <> transfer.`did` )
CREATE TEMPORARY VIEW `condition_2` AS ( SELECT * FROM condition_1 WHERE id IN ( SELECT id FROM comparison_2 ) )
CREATE TEMPORARY VIEW `action_1` AS ( SELECT `id`,`accountnumber`,sourcetime,PROCTIME() AS resulttime FROM condition_2 )
INSERT INTO alert SELECT * FROM action_1
