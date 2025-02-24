from typing import List, Dict, Any, Tuple
import asyncio

from .RPCRequestManager import RPCRequestManager
from .utils.RPC.RPCRequests import *

class RPCClient(RPCRequestManager):
    def __init__(self, endpoints_file: str = None, endpoints_list: List[Tuple[str, int]] = None):
        """
        Initializes the RPCClient with either a file containing endpoints or a list of (url, rps) tuples.
        
        :param endpoints_file: Path to a file containing endpoint URLs and RPS values.
        :param endpoints_list: List of tuples containing (url, rps) for endpoints.
        """
        super().__init__(endpoints_file, endpoints_list)
    

    async def get_tx_signatures(self, address, before=None, until=None, timestamp=None, limit=None):
        """
        Fetches transaction signatures for an address, starting from `before` and stopping at `until` or `timestamp`.
        
        :param address: Address of the account to fetch signatures for.
        :param before: Transaction signature to start fetching from (fetches older transactions).
        :param until: Transaction signature to stop at.
        :param timestamp: Unix timestamp to stop at. ISSUE: with getblock.io I was getting inconsistent results when using timestamp param
        :param limit: Maximum number of transaction signatures to fetch.
        
        :return: List of transaction signatures that match the conditions, excludes error txs, in order from oldest to newest.
        """
        all_signatures = []
        total_fetched = 0

        while True:
            # Prepare the request with the current `end_sig` (fetch older transactions)
            request = getSignaturesForAddressRequest(address, before=before, until=until)
            signatures = await self._send_request(request)
            # Stop if no signatures are returned, this handles until being hit
            if not signatures or len(signatures) == 0:
                break
            total_fetched += len(signatures)
            print(f"Fetched {total_fetched} signatures so far...", end='\r')
            # Sort by timestamp
            signatures.sort(key=lambda x: x.slot)
            
            # Filter signatures that don't have errors
            valid_sigs = [sig for sig in signatures if sig.err is None]
            
            # Add valid signatures to the result
            if valid_sigs:
                all_signatures.extend(valid_sigs)
            
            # Get the oldest signature, we sorted so smallest blocktime fist i.e oldest tx
            end_signature = signatures[0]
            before = end_signature.signature
            
            # If `timestamp` is provided, check if we should stop based on block time
            if timestamp and end_signature.block_time < timestamp:
                break

            if len(signatures) < 1000:  # If get signatures for address returns less than 1000 it means we've reached last page of signatures
                break

            if limit and len(all_signatures) >= limit:
                break
        
        # If `timestamp` is provided, filter the signatures again to only return those after the timestamp
        if timestamp:
            all_signatures = [sig for sig in all_signatures if sig.block_time >= timestamp]
        
        if limit:
            all_signatures = all_signatures[:limit]
        
        print("")  # Progress print uses carriage return so add empty so outside of the fuction prints work
        return [sig.signature for sig in sorted(all_signatures, key=lambda x: x.slot)]
    
    async def get_tx_signatures_yield(self, address, before=None, until=None, timestamp=None, limit=None, yield_amount=None):
        """
        Fetches transaction signatures for an address, starting from `before` and stopping at `until` or `timestamp`.
        
        :param address: Address of the account to fetch signatures for.
        :param before: Transaction signature to start fetching from (fetches older transactions).
        :param until: Transaction signature to stop at.
        :param timestamp: Unix timestamp to stop at. ISSUE: with getblock.io I was getting inconsistent results when using timestamp param
        :param limit: Maximum number of transaction signatures to fetch.
        :param yield_amount: Number of sigs to yield at a time, default is it yields everytime it gets new sigs
        
        :return: List of transaction signatures that match the conditions, excludes error txs, in order from oldest to newest.


        NOTE Wasn't written to work properly with timestamp and limit so may get more txs than limit and txs not within timestamp cutoff
        """
        all_signatures = []
        total_fetched = 0
        num_yielded = 0

        while True:
            # Prepare the request with the current `end_sig` (fetch older transactions)
            request = getSignaturesForAddressRequest(address, before=before, until=until)
            signatures = await self._send_request(request)
            # Stop if no signatures are returned, this handles until being hit
            if not signatures or len(signatures) == 0:
                break
            total_fetched += len(signatures)
            print(f"Fetched {total_fetched} signatures so far...", end='\r')
            # Sort by timestamp
            signatures.sort(key=lambda x: x.slot)
            
            # Filter signatures that don't have errors
            valid_sigs = [sig for sig in signatures if sig.err is None]
            
            # Add valid signatures to the result
            if valid_sigs:
                all_signatures.extend(valid_sigs)
                if yield_amount:
                    if len(all_signatures) - num_yielded > yield_amount:
                        yield [sig.signature for sig in all_signatures[num_yielded: num_yielded + yield_amount]]
                        num_yielded += yield_amount

                else:
                    yield [sig.signature for sig in valid_sigs]
            
            # Get the oldest signature, we sorted so smallest blocktime fist i.e oldest tx
            end_signature = signatures[0]
            before = end_signature.signature
            
            # If `timestamp` is provided, check if we should stop based on block time
            if timestamp and end_signature.block_time < timestamp:
                break

            if len(signatures) < 1000:  # If get signatures for address returns less than 1000 it means we've reached last page of signatures
                break

            if limit and len(all_signatures) >= limit:
                break
        
        print("")  # Progress print uses carriage return so add empty so outside of the fuction prints work
        
        # If yield_amount is set we may get here with some not yielded
        if yield_amount and num_yielded < len(all_signatures):
            yield [sig.signature for sig in all_signatures[num_yielded:]]
    
    async def get_batched_tx_signatures(self, address, before, until, avg_sigs_per_block=None):
        """
        For a given address and start and end signatures, it attempts to split the fetching process into chunks 
        to be processed in parallel.
        
        :param address: The address of the account we want to fetch signatures for.
        :param before: Start searching backwards in time from this "before" signature.
        :param until: Search until this "until" signature is found.
        :param avg_sigs_per_block: Estimate of average times a tx of the given address is found within 1 block,
        this is used to determine how many chunks to split it up into (if address isn't frequent -> more chunks is less efficient).
        
        :return: List of transaction signatures that match the conditions, excludes error txs, in order from oldest to newest.
        """
        request = getTransactionRequest(before)
        before_tx = await self._send_request(request)
        if not before_tx:
            e = f"Unable to determine which slot, before signature: {before} is in."
            print(f"Error occured during batch method, using standard method get_tx_signatures instead, error: {e}")
            return await self.get_tx_signatures(address, before=before, until=until)

        request = getTransactionRequest(until)
        until_tx = await self._send_request(request)
        if not until_tx:
            e = f"Unable to determine which slot, until signature: {until} is in."
            print(f"Error occured during batch method, using standard method get_tx_signatures instead, error: {e}")
            return await self.get_tx_signatures(address, before=before, until=until)

        slot_span = before_tx.slot - until_tx.slot
        if avg_sigs_per_block:
            estimated_txs_to_fetch = slot_span * avg_sigs_per_block
        else:
            estimated_txs_to_fetch = slot_span  # Assume average of 1 tx every block

        # Each request gets 1000, so split into 100,000 sections
        num_of_sections = max(1, estimated_txs_to_fetch // 100000)

        if num_of_sections >= 2:
            try:
                sections_sig_bounds = await self.get_signature_sections(
                    before, until, before_tx.slot, until_tx.slot, num_of_sections
                )
            except ValueError as e:
                print(f"Error occured during batch method, using standard method get_tx_signatures instead, error: {e}")
                return await self.get_tx_signatures(address, before=before, until=until)


            # Use a wrapper to include section ID for sorting later
            async def fetch_with_section_id(section_id, bounds):
                try:
                    signatures = await self.get_tx_signatures(address, before=bounds[1], until=bounds[0])
                    return section_id, signatures
                except Exception as e:
                    raise RuntimeError(f"Error fetching signatures for section {section_id}: {e}")

            # Fetch all sections concurrently
            print(f"Estimated: {estimated_txs_to_fetch} txs to fetch, splitting into {len(sections_sig_bounds)} sections")
            request_tasks = [fetch_with_section_id(section_id, bounds) for section_id, bounds in sections_sig_bounds.items()]
            responses = await asyncio.gather(*request_tasks, return_exceptions=True)

            # Handle exceptions
            for response in responses:
                if isinstance(response, Exception):
                    print(f"Error occured during batch method, using standard method get_tx_signatures instead, error: {response}")
                    return await self.get_tx_signatures(address, before=before, until=until)

            # Sort and merge results
            signatures = []
            for section_id, section_signatures in sorted(responses, key=lambda x: x[0]):
                signatures.extend(section_signatures)

            return signatures
        
        # If there's no point in splitting into sections, use default method
        print(f"Batch method will be inefficient, using standard method get_tx_signatures instead")
        return await self.get_tx_signatures(address, before=before, until=until)

    
    '''async def get_signature_sections(self, sig1, sig2, slot1, slot2, num_of_sections: int):
        """
        Given a start and end signature, splits it into num_of_sections where each section has a lower and upper tx sig bounding it
        
        :param sig1: Starting signature, newest
        :param sig2: Ending signature, oldest
        :param slot1: Starting slot, newest
        :param slot2: Ending slot, oldest
        :param num_of_sections: How many sections we want to split the signature bounds into
        
        :return: List of RPCSignature pairs, where a pair is the upper and lower bound of the section
        """

        length = slot1 - slot2
        section_size = length / num_of_sections

        sections_slot_bounds = []
        sections_sig_bounds = {}

        for i in range(0, num_of_sections):
            sections_slot_bounds.append((int(i * section_size + slot2), int((i + 1) * section_size + slot2)))

        for index, slot_bounds in enumerate(sections_slot_bounds):
            if index == 0:
                before = await self.get_nearest_sig(slot_bounds[1])
                until = sig2
            elif index == num_of_sections - 1:
                before = sig1
                until = sections_sig_bounds[index - 1][1]  # Use previous upper bound as last sections lower bound
            else:
                before = await self.get_nearest_sig(slot_bounds[1])
                until = sections_sig_bounds[index - 1][1] # Use previous upper bound as any middle sections lower bound

            sections_sig_bounds[index] = (until, before)

            if before is None:
                raise ValueError(
                    f"Unable to determine a valid signature near slot {slot_bounds[1]} for section {index}."
                )
        
        return sections_sig_bounds'''
    
    async def get_signature_sections(self, sig1, sig2, slot1, slot2, num_of_sections: int):
        """
        Given a start and end signature, splits it into num_of_sections where each section has a lower and upper tx sig bounding it.
        If a section cannot be determined due to missing signature bounds, it is merged with the subsequent section.

        :param sig1: Starting signature, newest
        :param sig2: Ending signature, oldest
        :param slot1: Starting slot, newest
        :param slot2: Ending slot, oldest
        :param num_of_sections: How many sections we want to split the signature bounds into

        :return: List of RPCSignature pairs, where a pair is the upper and lower bound of the section
        """

        length = slot1 - slot2
        section_size = length / num_of_sections

        sections_slot_bounds = []
        sections_sig_bounds = {}

        for i in range(num_of_sections):
            start_slot = int(i * section_size + slot2)
            end_slot = int((i + 1) * section_size + slot2)
            sections_slot_bounds.append((start_slot, end_slot))

        current_start_sig = sig2
        current_start_slot = slot2

        section_num = 0
        for index, slot_bounds in enumerate(sections_slot_bounds):
            if index == num_of_sections - 1:
                # Last section
                end_sig = sig1
                end_slot = slot1
            else:
                end_slot = slot_bounds[1]
                end_sig = await self.get_nearest_sig(end_slot)

                if end_sig is None:
                    # Skip this section and merge it with the next
                    continue

            sections_sig_bounds[section_num] = (current_start_sig, end_sig)
            current_start_sig = end_sig
            current_start_slot = end_slot

            section_num += 1  # Increment section num everytime we create valid section

        # If no valid sections could be formed
        if not sections_sig_bounds:
            raise ValueError("Unable to determine valid sections with the given parameters.")

        return sections_sig_bounds

    
    async def get_nearest_sig(self, slot, max_distance=10):
        """
        Given a slot, it finds the closest valid block and takes a signature from there
        
        :param tx1: slot we want to find a signature near to
        :param max_distance: how many slots the sig can be away from slot before stopping and returning none instead
        
        :return: transaction signature
        """
        i = 0
        while i < max_distance:
            request = getBlockRequest(slot + i, transaction_details="signatures")
            block = await self._send_request(request)
            if block and len(block.signatures) > 0:
                return block.signatures[0]

            request = getBlockRequest(slot - i, transaction_details="signatures")
            block = await self._send_request(request)
            if block and len(block.signatures) > 0:
                return block.signatures[0]
            i += 1
        
        return None
    

async def example_usage():
    # Example usage
    url = "Enter endpoint url here"
    rps = 100 # 300 requests per second
    rpc_client = RPCClient(endpoints_list=[(url, rps)])  # Can add as many endpoints as your wan't

    # Example getting signatures
    address = "EbKMvAhk3spSTFBokJQbnmZzvSoyCYnzjzd3Rx9BvB9e"

    signatures = await rpc_client.get_tx_signatures(address)

    # Fetch transactions
    requests = [getTransactionRequest(sig) for sig in signatures]
    excluded_endpoints = ["add endpoint url to not use here"]
    transactions = await rpc_client.distribute_and_send_requests(requests, excluded_endpoints=excluded_endpoints)

if __name__ == "__main__":
    asyncio.run(example_usage())