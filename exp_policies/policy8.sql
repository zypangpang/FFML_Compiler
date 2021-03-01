CREATE TEMPORARY VIEW `event_1` AS ( SELECT * FROM transfer WHERE channel='ONL' )
CREATE TEMPORARY VIEW `procedure_1` AS ( SELECT accountnumber, COUNT(*) AS `transcount`, TUMBLE_END(rowtime, INTERVAL '3' DAY) AS rowtime FROM event_1 GROUP BY accountnumber,TUMBLE(rowtime, INTERVAL '3' DAY) )
CREATE TEMPORARY VIEW `procedure_2` AS ( SELECT accountnumber, `transcount`, rowtime FROM ( SELECT *, ROW_NUMBER() OVER(PARTITION BY accountnumber ORDER BY rowtime DESC) as rownum FROM procedure_1 ) WHERE rownum <= 1 )
CREATE TEMPORARY VIEW `comparison_1` AS ( SELECT accountnumber, rowtime FROM procedure_2 WHERE `transcount` > 10.0 )
CREATE TEMPORARY VIEW `cast_1` AS ( SELECT id,accountnumber, CAST(rowtime AS TIMESTAMP(3)) AS rowtime FROM event_1 )
CREATE TEMPORARY VIEW `cast_2` AS ( SELECT accountnumber, CAST(rowtime AS TIMESTAMP(3)) AS rowtime FROM comparison_1 )
CREATE TEMPORARY VIEW `condition_1` AS ( SELECT cast_1.* FROM cast_2,cast_1 WHERE cast_2.accountnumber=cast_1.accountnumber AND cast_1.rowtime >= cast_2.rowtime )
CREATE TEMPORARY VIEW `condition_2` AS ( SELECT * FROM event_1 WHERE id IN ( SELECT id FROM condition_1 ) )
CREATE TEMPORARY VIEW `procedure_3` AS ( SELECT id,rowtime, FOREIGNIP(dest_ip) as fip FROM condition_2 )
CREATE TEMPORARY VIEW `comparison_2` AS ( SELECT id, rowtime FROM procedure_3 WHERE `fip` = TRUE )
CREATE TEMPORARY VIEW `condition_3` AS ( SELECT * FROM condition_2 WHERE id IN ( SELECT id FROM comparison_2 ) )
CREATE TEMPORARY VIEW `comparison_3` AS ( SELECT id, rowtime FROM transfer WHERE `value` < 10000.0 )
CREATE TEMPORARY VIEW `condition_4` AS ( SELECT * FROM condition_3 WHERE id IN ( SELECT id FROM comparison_3 ) )
CREATE TEMPORARY VIEW `action_1` AS ( SELECT `id`,`accountnumber`,sourcetime,PROCTIME() AS resulttime FROM condition_4 )
INSERT INTO alert SELECT * FROM action_1
