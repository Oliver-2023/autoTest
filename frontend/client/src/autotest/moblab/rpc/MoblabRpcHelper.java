package autotest.moblab.rpc;

import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;

import autotest.common.JsonRpcCallback;
import autotest.common.JsonRpcProxy;
import autotest.common.SimpleCallback;

import java.util.Map;

/**
 * A helper class for moblab RPC call.
 */
public class MoblabRpcHelper {
  public static final String RPC_PARAM_CLOUD_STORAGE_INFO = "cloud_storage_info";

  private MoblabRpcHelper() {}

  /**
   * Fetches config data.
   */
  public static void fetchConfigData(final SimpleCallback callback) {
    fetchConfigData(new JsonRpcCallback() {
      @Override
      public void onSuccess(JSONValue result) {
        if (callback != null)
          callback.doCallback(result);
      }
    });
  }

  /**
   * Fetch config data.
   */
  public static void fetchConfigData(final JsonRpcCallback callback) {
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("get_config_values", null, callback);
  }

  /**
   * Submits config data.
   */
  public static void submitConfigData(JSONObject configValues, JsonRpcCallback callback) {
    JSONObject params = new JSONObject();
    params.put("config_values", configValues);
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("update_config_handler", params, callback);
  }

  /**
   * Resets config data on Moblab.
   */
  public static void resetConfigData(final JsonRpcCallback callback) {
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("reset_config_settings", null, callback);
  }

  /**
   * Reboot Moblab device.
   */
  public static void rebootMoblab(final JsonRpcCallback callback) {
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("reboot_moblab", null, callback);
  }

  /**
   * Fetches the server network information.
   */
  public static void fetchNetworkInfo(
      final MoblabRpcCallbacks.FetchNetworkInfoRpcCallback callback) {
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("get_network_info", null, new JsonRpcCallback() {
      @Override
      public void onSuccess(JSONValue result) {
        NetworkInfo networkInfo = new NetworkInfo();
        networkInfo.fromJson(result.isObject());
        callback.onNetworkInfoFetched(networkInfo);
      }
    });
  }

  /**
   * Fetches the cloud storage configuration information.
   */
  public static void fetchCloudStorageInfo(
      final MoblabRpcCallbacks.FetchCloudStorageInfoCallback callback) {
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("get_cloud_storage_info", null, new JsonRpcCallback() {
      @Override
      public void onSuccess(JSONValue result) {
        CloudStorageInfo info = new CloudStorageInfo();
        info.fromJson(result.isObject());
        callback.onCloudStorageInfoFetched(info);
      }
    });
  }

  /**
   * Validates the cloud storage configuration information.
   */
  public static void validateCloudStorageInfo(CloudStorageInfo cloudStorageInfo,
      final MoblabRpcCallbacks.ValidateCloudStorageInfoCallback callback) {
    JSONObject params = new JSONObject();
    params.put(RPC_PARAM_CLOUD_STORAGE_INFO, cloudStorageInfo.toJson());
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("validate_cloud_storage_info", params, new JsonRpcCallback() {
      @Override
      public void onSuccess(JSONValue result) {
        OperationStatus status = new OperationStatus();
        status.fromJson(result.isObject());
        callback.onCloudStorageInfoValidated(status);
      }
    });
  }

  /**
   * Submits the wizard configuration data.
   */
  public static void submitWizardConfigData(Map<String, JSONObject> configDataMap,
      final MoblabRpcCallbacks.SubmitWizardConfigInfoCallback callback) {
    JSONObject params = new JSONObject();
    if (configDataMap.containsKey(RPC_PARAM_CLOUD_STORAGE_INFO)) {
      params.put(RPC_PARAM_CLOUD_STORAGE_INFO, configDataMap.get(RPC_PARAM_CLOUD_STORAGE_INFO));
    } else {
      params.put(RPC_PARAM_CLOUD_STORAGE_INFO, new JSONObject());
    }
    JsonRpcProxy rpcProxy = JsonRpcProxy.getProxy();
    rpcProxy.rpcCall("submit_wizard_config_info", params, new JsonRpcCallback() {
      @Override
      public void onSuccess(JSONValue result) {
        OperationStatus status = new OperationStatus();
        status.fromJson(result.isObject());
        callback.onWizardConfigInfoSubmitted(status);
      }
    });
  }
}
