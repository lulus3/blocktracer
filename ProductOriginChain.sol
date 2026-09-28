// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title ProductOriginChain
/// @notice Registro e rastreabilidade de produtos em uma rede Ethereum local.
contract ProductsOriginChain {
    enum ProductStatus {
        Active,
        Recalled
    }

    struct Product {
        bool exists;
        string productId;
        string productName;
        string batchNumber;
        string manufactureDate;
        string manufacturerName;
        string manufacturingLocation;
        string briefDescription;
        address manufacturerAccount;
        address currentCustodian;
        uint256 registeredAt;
        ProductStatus status;
    }

    struct CustodyRecord {
        address from;
        address to;
        string location;
        uint256 timestamp;
    }

    struct Participant {
        bool exists;
        string name;
        string organization;
    }

    address public owner;
    mapping(address => bool) public authorizedManufacturers;
    mapping(address => bool) public authorizedCustodians;
    mapping(address => Participant) private participants;
    mapping(string => Product) private products;
    mapping(string => CustodyRecord[]) private custodyHistory;
    string[] private registeredProductIds;

    event ManufacturerAuthorizationUpdated(address indexed account, bool authorized);
    event CustodianAuthorizationUpdated(address indexed account, bool authorized);
    event ParticipantRegistered(address indexed account, string name, string organization);
    event ProductRegistered(
        string indexed productId,
        string productName,
        string batchNumber,
        address indexed manufacturer,
        uint256 registeredAt
    );
    event CustodyTransferred(
        string indexed productId,
        address indexed from,
        address indexed to,
        string location,
        uint256 timestamp
    );
    event ProductRecalled(string indexed productId, address indexed recalledBy, uint256 timestamp);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the administrator can perform this action");
        _;
    }

    modifier onlyAuthorizedManufacturer() {
        require(authorizedManufacturers[msg.sender], "Unauthorized manufacturer");
        _;
    }

    modifier onlyAuthorizedCustodian() {
        require(authorizedCustodians[msg.sender], "Unauthorized custodian");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedManufacturers[msg.sender] = true;
        authorizedCustodians[msg.sender] = true;
        participants[msg.sender] = Participant({
            exists: true,
            name: "Administrador local",
            organization: "ProductOriginChain"
        });
        emit ManufacturerAuthorizationUpdated(msg.sender, true);
        emit CustodianAuthorizationUpdated(msg.sender, true);
        emit ParticipantRegistered(msg.sender, "Administrador local", "ProductOriginChain");
    }

    /// @notice Cria ou atualiza a identificação e as permissões de um participante da rede local.
    function registerParticipant(
        address account,
        string calldata name,
        string calldata organization,
        bool manufacturerAuthorized,
        bool custodianAuthorized
    ) external onlyOwner {
        require(account != address(0), "Invalid account");
        require(bytes(name).length > 0, "Participant name is required");
        require(bytes(organization).length > 0, "Organization is required");

        participants[account] = Participant({exists: true, name: name, organization: organization});
        authorizedManufacturers[account] = manufacturerAuthorized;
        authorizedCustodians[account] = custodianAuthorized;

        emit ParticipantRegistered(account, name, organization);
        emit ManufacturerAuthorizationUpdated(account, manufacturerAuthorized);
        emit CustodianAuthorizationUpdated(account, custodianAuthorized);
    }

    function setManufacturer(address account, bool authorized) external onlyOwner {
        require(account != address(0), "Invalid account");
        require(participants[account].exists, "Participant must be identified first");
        authorizedManufacturers[account] = authorized;
        emit ManufacturerAuthorizationUpdated(account, authorized);
    }

    function setCustodian(address account, bool authorized) external onlyOwner {
        require(account != address(0), "Invalid account");
        require(participants[account].exists, "Participant must be identified first");
        authorizedCustodians[account] = authorized;
        emit CustodianAuthorizationUpdated(account, authorized);
    }

    function register(
        string calldata productId,
        string calldata productName,
        string calldata batchNumber,
        string calldata manufactureDate,
        string calldata manufacturerName,
        string calldata manufacturingLocation,
        string calldata briefDescription
    ) external onlyAuthorizedManufacturer {
        require(bytes(productId).length > 0, "Product ID is required");
        require(bytes(productName).length > 0, "Product name is required");
        require(bytes(batchNumber).length > 0, "Batch number is required");
        require(!products[productId].exists, "Product ID already registered");

        products[productId] = Product({
            exists: true,
            productId: productId,
            productName: productName,
            batchNumber: batchNumber,
            manufactureDate: manufactureDate,
            manufacturerName: manufacturerName,
            manufacturingLocation: manufacturingLocation,
            briefDescription: briefDescription,
            manufacturerAccount: msg.sender,
            currentCustodian: msg.sender,
            registeredAt: block.timestamp,
            status: ProductStatus.Active
        });
        registeredProductIds.push(productId);

        custodyHistory[productId].push(
            CustodyRecord({from: address(0), to: msg.sender, location: manufacturingLocation, timestamp: block.timestamp})
        );

        emit ProductRegistered(productId, productName, batchNumber, msg.sender, block.timestamp);
    }

    function getProductSummary(string calldata productId)
        external
        view
        returns (
            bool exists,
            string memory storedProductId,
            string memory productName,
            string memory batchNumber,
            uint256 registeredAt,
            ProductStatus status
        )
    {
        Product storage product = products[productId];
        return (
            product.exists,
            product.productId,
            product.productName,
            product.batchNumber,
            product.registeredAt,
            product.status
        );
    }

    function getProductDetails(string calldata productId)
        external
        view
        returns (
            string memory manufactureDate,
            string memory manufacturerName,
            string memory manufacturingLocation,
            string memory briefDescription,
            address manufacturerAccount,
            address currentCustodian
        )
    {
        Product storage product = products[productId];
        require(product.exists, "Product not found");
        return (
            product.manufactureDate,
            product.manufacturerName,
            product.manufacturingLocation,
            product.briefDescription,
            product.manufacturerAccount,
            product.currentCustodian
        );
    }

    /// @notice Retorna quantos produtos foram registrados no contrato.
    function getProductCount() external view returns (uint256) {
        return registeredProductIds.length;
    }

    /// @notice Consulta a identificação e as permissões atuais associadas a uma carteira.
    function getParticipant(address account)
        external
        view
        returns (
            bool exists,
            string memory name,
            string memory organization,
            bool isManufacturer,
            bool isCustodian
        )
    {
        Participant storage participant = participants[account];
        return (
            participant.exists,
            participant.name,
            participant.organization,
            authorizedManufacturers[account],
            authorizedCustodians[account]
        );
    }

    /// @notice Retorna o ID de um produto pelo índice para permitir consulta paginada pela interface.
    function getProductIdAt(uint256 index) external view returns (string memory) {
        require(index < registeredProductIds.length, "Product index out of bounds");
        return registeredProductIds[index];
    }

    function transferCustody(string calldata productId, address newCustodian, string calldata location)
        external
        onlyAuthorizedCustodian
    {
        Product storage product = products[productId];
        require(product.exists, "Product not found");
        require(product.status == ProductStatus.Active, "Recalled products cannot be transferred");
        require(product.currentCustodian == msg.sender, "Only the current custodian can transfer");
        require(authorizedCustodians[newCustodian], "Destination custodian is not authorized");
        require(newCustodian != address(0), "Invalid destination account");
        require(bytes(location).length > 0, "Location is required");

        address previousCustodian = product.currentCustodian;
        product.currentCustodian = newCustodian;
        custodyHistory[productId].push(
            CustodyRecord({from: previousCustodian, to: newCustodian, location: location, timestamp: block.timestamp})
        );

        emit CustodyTransferred(productId, previousCustodian, newCustodian, location, block.timestamp);
    }

    function recallProduct(string calldata productId) external {
        Product storage product = products[productId];
        require(product.exists, "Product not found");
        require(msg.sender == owner || msg.sender == product.manufacturerAccount, "Unauthorized recall");
        require(product.status == ProductStatus.Active, "Product already recalled");

        product.status = ProductStatus.Recalled;
        emit ProductRecalled(productId, msg.sender, block.timestamp);
    }

    function getCustodyHistoryCount(string calldata productId) external view returns (uint256) {
        return custodyHistory[productId].length;
    }

    function getCustodyRecord(string calldata productId, uint256 index)
        external
        view
        returns (address from, address to, string memory location, uint256 timestamp)
    {
        require(index < custodyHistory[productId].length, "History index out of bounds");
        CustodyRecord storage record = custodyHistory[productId][index];
        return (record.from, record.to, record.location, record.timestamp);
    }
}
