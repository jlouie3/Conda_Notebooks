
DECLARE @TotalTransactions DECIMAL(19,9) = (SELECT COUNT(DISTINCT TransactionId) FROM ProductTransaction);
DECLARE @MIN_SUPPORT DECIMAL(19,9) = .001;		-- Used to filter out unpopular items or outliers and save on computation
DECLARE @MIN_CONFIDENCE DECIMAL(19,9) = .010;	-- Used to filter out any rules that are not compelling enough

SELECT 
	ItemId 
	,COUNT(*) / @TotalTransactions AS Support
INTO mba.Set_1_Support 
FROM ProductTransaction
GROUP BY ItemId
HAVING COUNT(*) / @TotalTransactions >= @MIN_SUPPORT;

ALTER TABLE mba.Set_1_Support
	ALTER COLUMN ItemId INT NOT NULL;
ALTER TABLE mba.Set_1_Support
	ADD CONSTRAINT PK_Set_1_Support PRIMARY KEY CLUSTERED (ItemId);
--
;WITH Set_2 AS (
	SELECT 
		s1.ItemId AS ItemId1
		,s2.ItemId AS ItemId2
	FROM (SELECT * FROM mba.Set_1_Support) s1
	CROSS JOIN (SELECT * FROM mba.Set_1_Support) s2
	WHERE s1.ItemId > s2.ItemId
)
SELECT 
	s.ItemId1
	,s.ItemId2 
	,COUNT(*) / @TotalTransactions AS Support
INTO mba.Set_2_Support
FROM Set_2 s
INNER JOIN ProductTransaction t1
ON t1.ItemId = s.ItemId1
INNER JOIN ProductTransaction t2
ON t2.ItemId = s.ItemId2
AND t2.TransactionId = t1.TransactionId
GROUP BY s.ItemId1, s.ItemId2
HAVING COUNT(*) / @TotalTransactions >= @MIN_SUPPORT;

ALTER TABLE mba.Set_2_Support
	ALTER COLUMN ItemId1 INT NOT NULL;
ALTER TABLE mba.Set_2_Support
	ALTER COLUMN ItemId2 INT NOT NULL;
ALTER TABLE mba.Set_2_Support
	ADD CONSTRAINT PK_Set_2_Support PRIMARY KEY CLUSTERED (ItemId1,ItemId2);

WITH Set_2_Confidence AS(
	SELECT 
		 s2.ItemId1
		,s2.ItemId2
		,s2.Support AS JointSupport
		,s2.Support / s1.Support AS Confidence
		,s1.Support AS Item1Support
	FROM mba.Set_2_Support s2
	INNER JOIN mba.Set_1_Support s1
	ON s1.ItemId = s2.ItemId1
)
SELECT 
	c.ItemId1 AS BasketItem1_Id
	,c.ItemId2 AS NextItem_Id
	,p1.ItemName AS BasketItem1
	,p2.ItemName AS NextItem
	,c.Confidence
	,c.JointSupport
	,c.Item1Support AS BasketItem1_Support
	,c.Confidence / c.Item1Support AS Lift
INTO mba.Set_2_Confidence
FROM Set_2_Confidence c
INNER JOIN Product p1
ON p1.ItemId = c.ItemId1
INNER JOIN Product p2
ON p2.ItemId = c.ItemId2
WHERE c.Confidence >= @MIN_CONFIDENCE
ORDER BY c.ItemId1, c.ItemId2

ALTER TABLE mba.Set_2_Confidence
	ALTER COLUMN BasketItem1_Id INT NOT NULL;
ALTER TABLE mba.Set_2_Confidence
	ADD CONSTRAINT PK_Set_2_Confidence PRIMARY KEY CLUSTERED (BasketItem1_Id);

--

WITH Set_3 AS (
	SELECT 
		s2.ItemId1
		,s2.ItemId2
		,ss2.ItemId1 AS ItemId3
	FROM mba.Set_2_Support s2
	CROSS JOIN (SELECT DISTINCT ItemId1 FROM mba.Set_2_Support) ss2
	WHERE s2.ItemId2 > ss2.ItemId1
)
SELECT 
	s.ItemId1
	,s.ItemId2
	,s.ItemId3
	,COUNT(*) / CONVERT(DECIMAL(19,9),@TotalTransactions) AS Support
INTO mba.Set_3_Support
FROM Set_3 s
INNER JOIN ProductTransaction t1
	ON t1.ItemId = s.ItemId1
INNER JOIN ProductTransaction t2
	ON t2.ItemId = s.ItemId2
	AND t2.TransactionId = t1.TransactionId
INNER JOIN ProductTransaction t3
	ON t3.ItemId = s.ItemId3
	AND t3.TransactionId = t2.TransactionId
	AND t3.TransactionId = t1.TransactionId
GROUP BY 
	s.ItemId1
	,s.ItemId2
	,s.ItemId3
HAVING COUNT(*) / @TotalTransactions >= @MIN_SUPPORT

-- Permute the set
INSERT INTO mba.Set_3_Support
SELECT
	ItemId1
	,ItemId3 AS ItemId2
	,ItemId2 AS ItemId3
FROM mba.Set_3_Support
UNION
SELECT
	ItemId2 AS ItemId1
	,ItemId3 AS ItemId2
	,ItemId1 AS ItemId3
FROM mba.Set_3_Support

ALTER TABLE mba.Set_3_Support
	ALTER COLUMN ItemId1 INT NOT NULL;
ALTER TABLE mba.Set_3_Support
	ALTER COLUMN ItemId2 INT NOT NULL;
ALTER TABLE mba.Set_3_Support
	ALTER COLUMN ItemId3 INT NOT NULL;
ALTER TABLE mba.Set_3_Support
	ADD CONSTRAINT PK_Set_3_Support PRIMARY KEY CLUSTERED (ItemId1,ItemId2,ItemId3);

WITH Set_3_Confidence AS(
	SELECT 
		 s3.ItemId1
		,s3.ItemId2
		,s3.ItemId3
		,s3.Support AS Set_3_Support
		,s3.Support / s2.Support AS Confidence
		,s2.Support AS Set_2_Support
	FROM mba.Set_3_Support s3
	INNER JOIN mba.Set_2_Support s2
	ON s2.ItemId1 = s3.ItemId1
	AND s2.ItemId2 = s3.ItemId2
	WHERE s3.Support >= @MIN_SUPPORT
)
SELECT 
	c.ItemId1 AS BasketItem1_Id
	,c.ItemId2 AS BasketItem2_Id
	,c.ItemId3 AS NextItem_Id
	,p1.ItemName AS BasketItem1
	,p2.ItemName AS BasketItem2
	,p3.ItemName AS NextItem
	,c.Confidence
	,c.Set_3_Support
	,c.Set_2_Support AS BasketItem1_Support
	,c.Confidence / c.Set_2_Support AS Lift
INTO mba.Set_3_Confidence
FROM Set_3_Confidence c
INNER JOIN Product p1
ON p1.ItemId = c.ItemId1
INNER JOIN Product p2
ON p2.ItemId = c.ItemId2
INNER JOIN Product p3
ON p3.ItemId = c.ItemId3
WHERE c.Confidence >= @MIN_CONFIDENCE
ORDER BY c.ItemId1, c.ItemId2

ALTER TABLE mba.Set_3_Confidence
	ALTER COLUMN BasketItem1_Id INT NOT NULL;
ALTER TABLE mba.Set_3_Confidence
	ADD CONSTRAINT PK_Set_3_Confidence PRIMARY KEY CLUSTERED (BasketItem1_Id,BasketItem2_Id);
