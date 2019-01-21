-- =============================================
-- Author:		Jon Louie
-- Create date: 12/31/18
-- Description:	Return number of transactions that appear with specified items
-- =============================================
CREATE FUNCTION fn_CountTransactionsWithItems
(	
	@item_ids VARCHAR(MAX) -- Comma delimited string of ItemIds
)
RETURNS INT 
AS
BEGIN
	DECLARE @result INT;

	;WITH ItemIds AS(
		SELECT VALUE AS ItemId FROM STRING_SPLIT(@item_ids,',')
	),
	TransactionsWithAllItems AS (
		SELECT t.TransactionId
		FROM TransactionsByDept t
		INNER JOIN ItemIds i
			ON i.ItemID = t.ItemId
		GROUP BY t.TransactionId
		HAVING COUNT(*) = (SELECT COUNT(*) FROM ItemIds)
	)
	SELECT @result = COUNT(*) FROM TransactionsWithAllItems 

	RETURN @result
END
GO
