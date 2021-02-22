CREATE TEMPORARY VIEW `event_1` AS ( SELECT * FROM `transfer` WHERE channel = 'ONL' )
CREATE TEMPORARY VIEW `event_2` AS ( SELECT * FROM event WHERE channel = 'ONL' )
CREATE TEMPORARY VIEW `event_3` AS ( SELECT * FROM event_2 MATCH_RECOGNIZE ( PARTITION BY accountnumber ORDER BY rowtime MEASURES transfer1.id as id,transfer1.rowtime AS rowtime ONE ROW PER MATCH AFTER MATCH SKIP PAST LAST ROW PATTERN (login1 login2 modify_password1 transfer1) WITHIN INTERVAL '5' MINUTE DEFINE login1 AS eventtype='login',login2 AS eventtype='login',modify_password1 AS eventtype='modify_password',transfer1 AS eventtype='transfer' ) )
CREATE TEMPORARY VIEW `event_4` AS ( SELECT * FROM event_1 WHERE id IN ( SELECT id FROM event_3 ) )
CREATE TEMPORARY VIEW `procedure_1` AS ( SELECT id,rowtime, SINGLELIMIT(accountnumber) as singlelimit FROM event_4 )
CREATE TEMPORARY VIEW `comparison_1` AS ( SELECT transfer.id AS id, transfer.rowtime AS rowtime FROM procedure_1, transfer WHERE procedure_1.id=transfer.id AND procedure_1.`singlelimit` < transfer.`value` )
CREATE TEMPORARY VIEW `condition_1` AS ( SELECT * FROM event_4 WHERE id IN ( SELECT id FROM comparison_1 ) )
CREATE TEMPORARY VIEW `action_1` AS ( SELECT `id`,`accountnumber`,sourcetime,PROCTIME() AS resulttime FROM condition_1 )
INSERT INTO alert SELECT * FROM action_1
