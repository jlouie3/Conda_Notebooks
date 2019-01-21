CREATE PROCEDURE SP_GetSupportForTransactionsByDeptSupport
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;
	
	DROP TABLE IF EXISTS SupportForTransactionsByDept;

	DECLARE @TotalTransactions DECIMAL(10,5) = 
		(SELECT COUNT(DISTINCT TransactionId) FROM TransactionsByDept);

	SELECT ItemId, COUNT(*)/@TotalTransactions AS Support 
	INTO SupportForTransactionsByDept
	FROM TransactionsByDept
	GROUP BY ItemId
	ORDER BY Support

	
	ALTER TABLE SupportForTransactionsByDept
	ALTER COLUMN ItemId INT NOT NULL;
	
	-- Use Dynamic SQL to prevent schema validation 
	-- (ALTER statement above is not registered during validation)
	EXEC('ALTER TABLE SupportForTransactionsByDept
		  ADD CONSTRAINT PK_SupportForTransactionsByDept PRIMARY KEY CLUSTERED (ItemId); ')

END
GO

exec SP_GetSupportForTransactionsByDeptSupport
