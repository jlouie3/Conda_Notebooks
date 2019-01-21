-- =============================================
-- Author:		Jon Louie
-- Create date: 12/31/18
-- Description:	Return support values for specified items that are above a threshold
-- =============================================
CREATE FUNCTION fn_CalculateItemSupport
(	
	@item_ids VARCHAR(MAX) -- Comma delimited string of ItemIds
)
RETURNS DECIMAL(19,9) 
AS
BEGIN
	DECLARE @result DECIMAL(19,9);
	SELECT @result = 
		dbo.fn_CountTransactionsWithItems(@item_ids) / CONVERT(DECIMAL(19,9),(SELECT COUNT(*) FROM TransactionsByDept))
	
	RETURN @result
END
GO
