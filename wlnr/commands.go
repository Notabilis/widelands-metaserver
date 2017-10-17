package main

const kRelayProtocolVersion uint8 = 1

// The commands used in the protocol
// The names match the names in the Widelands sources
// Keep this synchronized with relay_protocol.h

// all
const kHello uint8 = 1
const kWelcome uint8 = 2
const kDisconnect uint8 = 3
// host
const kConnectClient uint8 = 11
const kDisconnectClient uint8 = 12
const kToClients uint8 = 13
const kFromClient uint8 = 14
const kPing uint8 = 15
const kPong uint8 = 16
// client
const kToHost uint8 = 21
const kFromHost uint8 = 22
