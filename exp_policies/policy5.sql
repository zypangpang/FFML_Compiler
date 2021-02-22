CREATE TEMPORARY VIEW `event_1` AS ( SELECT * FROM transfer WHERE channel='ONL' )
CREATE TEMPORARY VIEW `procedure_1` AS ( SELECT S.id,S.rowtime,T.v as transcount FROM event_1 as S, LATERAL TABLE(TRANSCOUNT(accountnumber,'ONL',3,1)) as T(v) )
CREATE TEMPORARY VIEW `comparison_1` AS ( SELECT id, rowtime FROM procedure_1 WHERE `transcount` > 3.0 )
CREATE TEMPORARY VIEW `condition_1` AS ( SELECT * FROM event_1 WHERE id IN ( SELECT id FROM comparison_1 ) )
CREATE TEMPORARY VIEW `procedure_2` AS ( SELECT S.id,S.rowtime,T.v as totaldebit FROM condition_1 as S, LATERAL TABLE(TOTALDEBIT(accountnumber,'ONL',3,1)) as T(v) )
CREATE TEMPORARY VIEW `comparison_2` AS ( SELECT id, rowtime FROM procedure_2 WHERE `totaldebit` >= 5000.0 )
CREATE TEMPORARY VIEW `condition_2` AS ( SELECT * FROM condition_1 WHERE id IN ( SELECT id FROM comparison_2 ) )
CREATE TEMPORARY VIEW `action_1` AS ( SELECT `id`,`accountnumber`,sourcetime,PROCTIME() AS resulttime FROM condition_2 )
INSERT INTO alert SELECT * FROM action_1
