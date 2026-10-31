// Fills in the address list and the collection table from the council's two endpoints.

const $ = (id) => document.getElementById(id);

async function post(path, fields) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(fields),
  });
  return response.json();
}

function say(text) {
  $("message").textContent = text;
}

function longDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });
}

$("postcode-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("address-form").hidden = true;
  $("results").hidden = true;
  const { addresses } = await post("api/addresses", { postcode: $("postcode").value });
  if (addresses.length === 0) {
    return say("We couldn't find any addresses for that postcode.");
  }
  say("");
  $("address").replaceChildren(
    ...addresses.map(({ uprn, address }) => new Option(address, uprn)),
  );
  $("address-form").hidden = false;
});

$("address-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const { address, collections } = await post("api/collections", { uprn: $("address").value });
  $("results-title").textContent = `Collections for ${address}`;
  document.querySelector("#results tbody").replaceChildren(
    ...collections.map(({ container, next_collection }) => {
      const row = document.createElement("tr");
      row.append(
        Object.assign(document.createElement("td"), { textContent: container }),
        Object.assign(document.createElement("td"), { textContent: longDate(next_collection) }),
      );
      return row;
    }),
  );
  $("results").hidden = false;
});
