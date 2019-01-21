/*
Support: Proportion of transactions containing some item(s) to the total number of transactions
		 Supp(A) = (# transactions containing A) / (# total transactions)
		 Supp(A,B) = (# transactions containing A and B) / (# total transactions)

Confidence: Likelihood of second item being bought once the first item is bought (aka conditional probability)
			Conf(B|A) = Supp(A,B) / Supp(A)

Lift: Change in likelihood of second item being bought once the first item is bought
	  Lift(B|A) = Conf(B|A) / Supp(A) = Supp(A,B) / Supp(A)^2

N-set: A set of N items (in this case it is a combination of a set of items)

Rule: An item or set of items that is shown to be a causal factor in purchasing another item
	  Ex: Consider the rule: Item1, Item2. This means Item1 has been shown increase chances of Item2 being bought.
		  Note that Rule(Item1,Item2) does NOT imply Rule(Item2,Item1) exists; these are NOT the same!
*/
DECLARE @TotalTransactions DECIMAL(19,9) = (SELECT COUNT(DISTINCT TransactionId) FROM ProductTransaction);
DECLARE @MIN_SUPPORT DECIMAL(19,9) = .010;		-- Used to filter out unpopular items or outliers and save on computation
DECLARE @MIN_CONFIDENCE DECIMAL(19,9) = .010;	-- Used to filter out any rules that are not compelling enough

WITH Support AS (
	SELECT 
		ItemId 
		,COUNT(*) / @TotalTransactions AS Support
	FROM ProductTransaction
	GROUP BY ItemId
)
,TwoSet AS (
	SELECT 
		s1.ItemId AS ItemId1
		,s2.ItemId AS ItemId2
	FROM (SELECT * FROM Support WHERE Support >= @MIN_SUPPORT) s1
	CROSS JOIN (SELECT * FROM Support WHERE Support >= @MIN_SUPPORT) s2
	WHERE s1.ItemId > s2.ItemId
	AND s1.Support >= @MIN_SUPPORT
	AND s2.Support >= @MIN_SUPPORT
)
,JointSupport AS (
	SELECT 
		ROW_NUMBER() OVER(ORDER BY ts.ItemId1, ts.ItemId2) AS JointSupportKey
		,ts.ItemId1
		,ts.ItemId2 
		,COUNT(*) / @TotalTransactions AS Support
	FROM TwoSet ts
	INNER JOIN ProductTransaction t1
	ON t1.ItemId = ts.ItemId1
	INNER JOIN ProductTransaction t2
	ON t2.ItemId = ts.ItemId2
	AND t2.TransactionId = t1.TransactionId
	GROUP BY ts.ItemId1, ts.ItemId2
)
,Confidence AS(
	SELECT 
		js.ItemId1
		,js.ItemId2
		,js.Support AS JointSupport
		,js.Support / s.Support AS Confidence
		,s.Support AS Item1Support
		,js.JointSupportKey
	FROM JointSupport js
	INNER JOIN Support s
	ON s.ItemId = js.ItemId1
	WHERE js.Support >= @MIN_SUPPORT
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
	,c.JointSupportKey
INTO mba.Recommended2Sets
FROM Confidence c
INNER JOIN Product p1
ON p1.ItemId = c.ItemId1
INNER JOIN Product p2
ON p2.ItemId = c.ItemId2
WHERE c.Confidence >= @MIN_CONFIDENCE
ORDER BY c.ItemId1, c.ItemId2
