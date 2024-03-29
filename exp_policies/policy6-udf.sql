CREATE TEMPORARY VIEW `event_1` AS ( SELECT * FROM transfer WHERE channel='ONL' )
CREATE TEMPORARY VIEW `procedure_1` AS ( SELECT S.id,S.rowtime,T.v as totaldebit FROM event_1 as S, LATERAL TABLE(TOTALDEBIT(accountnumber,'ONL',1,1)) as T(v) )
CREATE TEMPORARY VIEW `math_1` AS ( SELECT transfer.id AS id,transfer.rowtime AS rowtime, procedure_1.`totaldebit` + transfer.`value` AS `result` FROM procedure_1 INNER JOIN transfer ON procedure_1.id = transfer.id )
CREATE TEMPORARY VIEW `comparison_1` AS ( SELECT id, rowtime FROM math_1 WHERE `result` >= 500.0 )
CREATE TEMPORARY VIEW `condition_1` AS ( SELECT * FROM event_1 WHERE id IN ( SELECT id FROM comparison_1 ) )
CREATE TEMPORARY VIEW `procedure_2` AS ( SELECT S.id,S.rowtime,T.v as totaldebit FROM condition_1 as S, LATERAL TABLE(TOTALDEBIT(accountnumber,'ONL',1,5)) as T(v) )
CREATE TEMPORARY VIEW `comparison_2` AS ( SELECT id, rowtime FROM procedure_2 WHERE `totaldebit` >= 250.0 )
CREATE TEMPORARY VIEW `count_1` AS ( SELECT id,MAX(rowtime) AS rowtime,COUNT(*) AS daycount FROM comparison_2 GROUP BY id,TUMBLE(rowtime, INTERVAL '1' SECOND) )
CREATE TEMPORARY VIEW `comparison_3` AS ( SELECT id, rowtime FROM count_1 WHERE `daycount` >= 3.0 )
CREATE TEMPORARY VIEW `condition_2` AS ( SELECT * FROM condition_1 WHERE id IN ( SELECT id FROM comparison_3 ) )
CREATE TEMPORARY VIEW `action_1` AS ( SELECT `id`,`accountnumber`,sourcetime,PROCTIME() AS resulttime FROM condition_2 )
INSERT INTO alert SELECT * FROM action_1
