"""
CREATE TABLE `statement_transactions` (
`id` int(11) NOT NULL,
`date` date NOT NULL,
`statement_month` int(11) NOT NULL,
`statement_year` int(11) NOT NULL,
`account_id` int(11) NOT NULL,
`amount` decimal(10,2) NOT NULL,
`description` text,
`taction_id` int(11), deferred tinyint(1) default 0,
PRIMARY KEY (`id`)
);
"""