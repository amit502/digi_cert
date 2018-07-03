const ipfs = require("nano-ipfs-store").at("https://ipfs.infura.io:5001");
const MyContract = artifacts.require("MyContract")

async function test() {
  const data = JSON.stringify({
    name: "JSON Statehem",
    link0: "stackexchange.com",
    link1: "github.com",
    link2: "myfacebook.com"
  })

  const ipfsHash = await ipfs.add(data)
  const instance = await MyContract.deployed()

  await instance.setHash.sendTransaction(ipfsHash)

  let returnedHash = await instance.ipfsHash.call()

  console.log(ipfsHash)
  console.log(returnedHash)

  console.log(JSON.parse(await ipfs.cat(returnedHash)))

}

test()